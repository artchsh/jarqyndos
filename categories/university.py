from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
import db
from utils import error_handler, validate_admin_action, ValidationError, validate_text, validate_url, logger
from helpers import confirm_deletion_handler

# Define conversation states
(NAME, INSTAGRAM) = range(2)

@error_handler
@validate_admin_action
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, replies: dict) -> None:
    """Display university administration menu"""
    logger.info(f"User {update.effective_user.id} accessed university admin menu")
    await update.callback_query.message.edit_text(
        "Университеты — выберите действие:", 
        reply_markup=replies["university_menu"]
    )
    context.user_data["current_category"] = "university"

@error_handler
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start university addition process"""
    await update.callback_query.message.edit_text(
        "Введите название университета:\n"
        "(или /cancel для отмены)"
    )
    return NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle university name input"""
    try:
        if not validate_text(update.message.text, min_length=2):
            raise ValidationError(
                "Название университета должно содержать минимум 2 символа.\n"
                "Пожалуйста, введите полное название."
            )
        
        context.user_data['university_data'] = {
            'name': update.message.text
        }
        
        await update.message.reply_text(
            "Теперь введите ссылку на Instagram студенческой организации:\n"
            "(или /cancel для отмены)"
        )
        return INSTAGRAM
        
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return NAME

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle university Instagram input and save university"""
    try:
        instagram = update.message.text
        if not validate_url(instagram) or len(instagram.split("@")) != 2:
            raise ValidationError("Некорректная ссылка. Должна начинаться с http://, https://, @")
        
        if instagram.startswith('@'):
            instagram = f"https://www.instagram.com/{instagram[1:]}"
            
        try:
            university_data = context.user_data['university_data']
            db.add_university(university_data['name'], instagram)
            
            logger.info(f"Added new university: {university_data['name']}")
            
            await update.message.reply_text(
                f"Университет '{university_data['name']}' успешно добавлен!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Назад", callback_data="admin_category_university")
                ]])
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error adding university: {str(e)}")
            await update.message.reply_text(
                "Произошла ошибка при сохранении. Попробуйте позже."
            )
            return ConversationHandler.END
            
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return INSTAGRAM

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Назад", callback_data="admin_category_university")
        ]])
    )
    return ConversationHandler.END

# Create conversation handler
university_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add, pattern="^add_university$")],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        INSTAGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    name="university_conversation",
    persistent=False,
)

@error_handler
async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle university deletion"""
    data = db.fetch_db()
    rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'university_info']
    if not rows:
        await update.callback_query.message.edit_text("Нет университетов для удаления.")
        return

    buttons = []
    delete_map = {}
    for idx, entry in enumerate(rows):
        key = str(idx)
        delete_map[key] = entry["info"]
        # Display just the university name in the button
        name = entry["info"]["name"] if isinstance(entry["info"], dict) else str(entry["info"])
        buttons.append([InlineKeyboardButton(name, callback_data=f'delete_university_{key}')])
    
    context.user_data['delete_universities'] = delete_map
    buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_university')])
    await update.callback_query.message.edit_text(
        "Выберите университет для удаления:", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@error_handler
async def confirm_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, replies: dict):
    """Handle university deletion confirmation"""
    await confirm_deletion_handler(
        update, context, 'delete_universities', 'university', replies["back_to_admin_menu"]
    )
