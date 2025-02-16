from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
import db
from utils import error_handler, validate_admin_action, ValidationError, validate_text, logger
from helpers import confirm_deletion_handler

# Define conversation states
(CONTACT,) = range(1)

@error_handler
@validate_admin_action
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, replies: dict) -> None:
    """Display contacts administration menu"""
    logger.info(f"User {update.effective_user.id} accessed contacts admin menu")
    await update.callback_query.message.edit_text(
        "Контакты — выберите действие:", 
        reply_markup=replies["contacts_menu"]
    )
    context.user_data["current_category"] = "contacts"

@error_handler
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start contact addition process"""
    await update.callback_query.message.edit_text(
        "Введите контактные данные:\n"
        "Можно отправить номер телефона или другую контактную информацию\n"
        "(или /cancel для отмены)"
    )
    return CONTACT

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle contact input and save"""
    try:
        if not validate_text(update.message.text, min_length=5):
            raise ValidationError(
                "Контактная информация должна содержать минимум 5 символов.\n"
                "Пожалуйста, введите более подробную информацию."
            )
        
        try:
            db.add_contact(update.message.text)
            logger.info(f"Added new contact by user {update.effective_user.id}")
            
            await update.message.reply_text(
                "Контакт успешно добавлен!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Назад", callback_data="admin_category_contacts")
                ]])
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error adding contact: {str(e)}")
            await update.message.reply_text(
                "Произошла ошибка при сохранении. Попробуйте позже."
            )
            return ConversationHandler.END
            
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return CONTACT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Назад", callback_data="admin_category_contacts")
        ]])
    )
    return ConversationHandler.END

# Create conversation handler
contacts_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add, pattern="^add_contacts$")],
    states={
        CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    name="contacts_conversation",
    persistent=False,
)

@error_handler
async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact deletion"""
    data = db.fetch_db()
    rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'contacts']
    if not rows:
        await update.callback_query.message.edit_text("Нет контактов для удаления.")
        return

    buttons = []
    delete_map = {}
    for idx, entry in enumerate(rows):
        key = str(idx)
        delete_map[key] = entry["info"]
        buttons.append([InlineKeyboardButton(entry["info"], callback_data=f'delete_contacts_{key}')])
    
    context.user_data['delete_contacts'] = delete_map
    buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_contacts')])
    await update.callback_query.message.edit_text(
        "Выберите контакт для удаления:", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@error_handler
async def confirm_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, replies: dict):
    """Handle contact deletion confirmation"""
    await confirm_deletion_handler(
        update, context, 'delete_contacts', 'contacts', replies["contacts_menu"]
    )
