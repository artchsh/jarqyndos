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
from utils import error_handler, validate_admin_action, ValidationError, validate_text, validate_url, logger
from helpers import confirm_deletion_handler

# Define conversation states
(NAME, SPECIALTY, INSTAGRAM, CONTACTS, PRICE) = range(5)

@error_handler
@validate_admin_action
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, replies: dict) -> None:
    """Display psychologist administration menu"""
    logger.info(f"User {update.effective_user.id} accessed psychologist admin menu")
    await update.callback_query.message.edit_text(
        "Психологи — выберите действие:", 
        reply_markup=replies["psychologist_menu"]
    )
    context.user_data["current_category"] = "psychologist"

@error_handler
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start psychologist addition process"""
    await update.callback_query.message.edit_text(
        "Введите имя и фамилию психолога:\n"
        "(или /cancel для отмены)"
    )
    return NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle psychologist name input"""
    try:
        if not validate_text(update.message.text, min_length=5):
            raise ValidationError(
                "Имя и фамилия должны содержать минимум 5 символов.\n"
                "Пожалуйста, введите полное имя."
            )
        
        context.user_data['psychologist_data'] = {
            'name': update.message.text
        }
        
        await update.message.reply_text(
            "Введите специализацию психолога:\n"
            "(или /cancel для отмены)"
        )
        return SPECIALTY
        
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return NAME

async def handle_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle psychologist specialty input"""
    try:
        if not validate_text(update.message.text, min_length=5):
            raise ValidationError(
                "Специализация должна содержать минимум 5 символов.\n"
                "Пожалуйста, опишите специализацию подробнее."
            )
        
        context.user_data['psychologist_data']['specialty'] = update.message.text
        
        await update.message.reply_text(
            "Введите Instagram психолога (или отправьте '-' если нет):\n"
            "(или /cancel для отмены)"
        )
        return INSTAGRAM
        
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return SPECIALTY

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle psychologist Instagram input"""
    try:
        instagram = update.message.text
        if instagram != '-' and not validate_url(instagram):
            raise ValidationError("Некорректная ссылка. Должна начинаться с @ или https://")
        
        context.user_data['psychologist_data']['instagram'] = instagram if instagram != '-' else None
        
        await update.message.reply_text(
            "Отправьте контакт психолога:\n"
            "Можно переслать контакт или написать номер телефона\n"
            "Отправьте '-' если не хотите указывать контакт\n"
            "(или /cancel для отмены)"
        )
        return CONTACTS
        
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return INSTAGRAM

async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle psychologist contacts input"""
    contact = None
    
    if update.message.contact:  # If user shared a contact
        contact = {
            'phone': update.message.contact.phone_number,
            'name': update.message.contact.full_name
        }
    elif update.message.text != '-':  # If user typed a phone number
        contact = {'phone': update.message.text}
        
    context.user_data['psychologist_data']['contacts'] = contact
    
    await update.message.reply_text(
        "Введите стоимость сессии:\n"
        "Введите число или 0 если цена не указана\n"
        "(или /cancel для отмены)"
    )
    return PRICE

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle psychologist price input and save psychologist"""
    try:
        price = int(update.message.text)
        if price < 0:
            raise ValueError("Цена не может быть отрицательной")
            
        psychologist_data = context.user_data['psychologist_data']
        
        try:
            db.add_psychologist(
                psychologist_data['name'],
                psychologist_data['specialty'],
                psychologist_data['instagram'],
                psychologist_data['contacts'],
                price if price > 0 else None
            )
            
            logger.info(f"Added new psychologist: {psychologist_data['name']}")
            
            await update.message.reply_text(
                "Психолог успешно добавлен!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Назад", callback_data="admin_category_psychologist")
                ]])
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error adding psychologist: {str(e)}")
            await update.message.reply_text(
                "Произошла ошибка при сохранении. Попробуйте позже."
            )
            return ConversationHandler.END
            
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите корректное число для цены:"
        )
        return PRICE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Назад", callback_data="admin_category_psychologist")
        ]])
    )
    return ConversationHandler.END

# Create conversation handler
psychologist_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add, pattern="^add_psychologist$")],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        SPECIALTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_specialty)],
        INSTAGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram)],
        CONTACTS: [
            MessageHandler(filters.CONTACT, handle_contacts),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contacts)
        ],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    name="psychologist_conversation",
    persistent=False,
)

# Keep existing delete handlers
@error_handler
async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle psychologist deletion"""
    data = db.fetch_db()
    rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'find_psychologist']
    if not rows:
        await update.callback_query.message.edit_text("Нет психологов для удаления.")
        return

    buttons = []
    delete_map = {}
    for idx, entry in enumerate(rows):
        key = str(idx)
        delete_map[key] = entry["info"]
        # Get name from either dict or legacy string format
        if isinstance(entry["info"], dict):
            name = entry["info"].get("name", "Неизвестный психолог")
        else:
            name = entry["info"].split("\n")[0] if "\n" in entry["info"] else entry["info"]
        buttons.append([InlineKeyboardButton(name, callback_data=f'delete_psychologist_{key}')])
    
    context.user_data['delete_psychologist'] = delete_map
    buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_psychologist')])
    await update.callback_query.message.edit_text(
        "Выберите психолога для удаления:", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@error_handler
async def confirm_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, replies: dict):
    """Handle psychologist deletion confirmation"""
    await confirm_deletion_handler(
        update, context, 'delete_psychologist', 'psychologist', replies["psychologist_menu"]
    )
