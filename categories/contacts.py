from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import db
from utils import error_handler, validate_admin_action, ValidationError, validate_text, logger
from helpers import confirm_deletion_handler

@error_handler
@validate_admin_action
async def admin_menu(update, context, replies):
    """Display contacts administration menu"""
    logger.info(f"User {update.effective_user.id} accessed contacts admin menu")
    await update.callback_query.message.edit_text(
        "Контакты — выберите действие:", 
        reply_markup=replies["contacts_menu"]
    )
    context.user_data["current_category"] = "contacts"

@error_handler
async def process_contact_input(update, context):
    """Process contact input with validation"""
    if not validate_text(update.message.text, min_length=5):
        raise ValidationError("Контактная информация должна содержать минимум 5 символов")
    
    try:
        db.add_bot_info('contacts', update.message.text)
        logger.info(f"Added new contact by user {update.effective_user.id}")
        await update.message.reply_text("Контакт успешно добавлен!")
    finally:
        context.user_data.pop('pending_admin_action', None)

@error_handler
async def add_handler(update, context):
    context.user_data['pending_admin_action'] = 'add_contacts'
    await update.callback_query.message.edit_text("Введите новые данные для контакта")

@error_handler
async def delete_handler(update, context):
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
async def confirm_delete_handler(update, context, replies):
    # Use "delete_contacts" as the key and "contacts" as the category.
    await confirm_deletion_handler(update, context, 'delete_contacts', 'contacts', replies["contacts_menu"])
