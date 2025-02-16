from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import db
from utils import error_handler, validate_admin_action, ValidationError, validate_text, logger
from helpers import confirm_deletion_handler

@error_handler
@validate_admin_action
async def admin_menu(update, context, replies):
    """Display practices administration menu"""
    logger.info(f"User {update.effective_user.id} accessed practices admin menu")
    await update.callback_query.message.edit_text(
        "Практики — выберите действие:", 
        reply_markup=replies["practices_menu"]
    )
    context.user_data["current_category"] = "practices"

@error_handler
async def add_handler(update, context):
    """Start practice addition process"""
    context.user_data['pending_admin_action'] = 'add_practices'
    context.user_data['practices_step'] = 'content'
    await update.callback_query.message.edit_text(
        "Введите текст практики.\n"
        "Можно использовать абзацы и форматирование."
    )

@error_handler
async def process_practice_input(update, context):
    """Process practice input with validation"""
    if not validate_text(update.message.text, min_length=10):
        raise ValidationError("Текст практики должен содержать минимум 10 символов")
    
    try:
        db.add_bot_info('practices', update.message.text)
        logger.info(f"Added new practice by user {update.effective_user.id}")
        await update.message.reply_text("Практика успешно добавлена!")
    finally:
        context.user_data.pop('pending_admin_action', None)
        context.user_data.pop('practices_step', None)

@error_handler
async def delete_handler(update, context):
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
        buttons.append([InlineKeyboardButton(entry["info"], callback_data=f'delete_practices_{key}')])
    context.user_data['delete_practices'] = delete_map
    buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_practices')])
    await update.callback_query.message.edit_text(
        "Выберите практику для удаления:", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@error_handler
async def confirm_delete_handler(update, context, replies):
    # Use "delete_practices" as the key and "practices" as the category.
    await confirm_deletion_handler(update, context, 'delete_practices', 'practices', replies["practices_menu"])
