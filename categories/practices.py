from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ReplyKeyboardRemove
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
(TITLE, CONTENT, AUTHOR) = range(3)

@error_handler
@validate_admin_action
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, replies: dict) -> None:
    """Display practices administration menu"""
    logger.info(f"User {update.effective_user.id} accessed practices admin menu")
    await update.callback_query.message.edit_text(
        "Практики — выберите действие:", 
        reply_markup=replies["practices_menu"]
    )
    context.user_data["current_category"] = "practices"

@error_handler
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start practice addition process"""
    await update.callback_query.message.edit_text(
        "Введите название практики:\n"
        "(или /cancel для отмены)"
    )
    return TITLE

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle practice title input"""
    try:
        if not validate_text(update.message.text, min_length=3):
            raise ValidationError(
                "Название практики должно содержать минимум 3 символа.\n"
                "Пожалуйста, введите более подробное название."
            )
        
        context.user_data['practice_data'] = {
            'name': update.message.text
        }
        
        await update.message.reply_text(
            "Теперь введите текст практики.\n"
            "Можно использовать абзацы и форматирование.\n"
            "(или /cancel для отмены)"
        )
        return CONTENT
        
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return TITLE

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle practice content input"""
    try:
        if not validate_text(update.message.text, min_length=10):
            raise ValidationError(
                "Текст практики должен содержать минимум 10 символов.\n"
                "Пожалуйста, опишите практику более подробно."
            )
        
        context.user_data['practice_data']['content'] = update.message.text
        
        await update.message.reply_text(
            "Введите автора практики (или отправьте '-' чтобы пропустить).\n"
            "По умолчанию будет указано ваше имя.\n"
            "(или /cancel для отмены)"
        )
        return AUTHOR
        
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return CONTENT

async def handle_author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle practice author input and save practice"""
    practice_data = context.user_data['practice_data']
    author = update.message.text
    
    if author == '-':
        practice_data['author'] = None
    else:
        practice_data['author'] = author or update.effective_user.full_name
        
    try:
        db.add_practice(
            practice_data['name'],
            practice_data['content'],
            practice_data['author']
        )
        
        author_info = f" от {practice_data['author']}" if practice_data.get('author') else ""
        logger.info(f"Added new practice '{practice_data['name']}'{author_info}")
        
        await update.message.reply_text(
            "Практика успешно добавлена!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Назад", callback_data="admin_category_practices")
            ]])
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error adding practice: {str(e)}")
        await update.message.reply_text(
            "Произошла ошибка при сохранении практики. Попробуйте позже."
        )
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Назад", callback_data="admin_category_practices")
        ]])
    )
    return ConversationHandler.END

# Create conversation handler
practice_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add, pattern="^add_practices$")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title)],
        CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_content)],
        AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_author)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    name="practice_conversation",
    persistent=False,
)

@error_handler
async def delete_handler(update: Update, context):
    data = db.fetch_db()
    rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'practices']
    if not rows:
        await update.callback_query.message.edit_text("Нет практик для удаления.")
        return

    buttons = []
    delete_map = {}
    for idx, entry in enumerate(rows):
        key = str(idx)
        delete_map[key] = entry["info"]
        # Get name from either dict or legacy string format
        if isinstance(entry["info"], dict):
            name = entry["info"].get("name", "Без названия")
            author = entry["info"].get("author", "")
            display_text = f"{name} (by {author})" if author else name
        else:
            display_text = str(entry["info"])
        buttons.append([InlineKeyboardButton(display_text, callback_data=f'delete_practices_{key}')])
    
    context.user_data['delete_practices'] = delete_map
    buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_practices')])
    await update.callback_query.message.edit_text(
        "Выберите практику для удаления:", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@error_handler
async def confirm_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, replies: dict):
    """
    Handle practice deletion confirmation.
    
    Args:
        update (Update): The update object from Telegram
        context (ContextTypes.DEFAULT_TYPE): The context object from Telegram
        replies (dict): Dictionary containing reply markup keyboards
    """
    await confirm_deletion_handler(update, context, 'delete_practices', 'practices', replies["practices_menu"])
