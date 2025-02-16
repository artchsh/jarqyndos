from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import db
from utils import error_handler, validate_admin_action, ValidationError, validate_text, validate_url, logger
from helpers import confirm_deletion_handler

@error_handler
@validate_admin_action
async def admin_menu(update, context, replies):
    """Display university administration menu"""
    logger.info(f"User {update.effective_user.id} accessed university admin menu")
    await update.callback_query.message.edit_text(
        "Университеты — выберите действие:", 
        reply_markup=replies["university_menu"]
    )
    context.user_data["current_category"] = "university"

async def add_handler(update, context):
    context.user_data['pending_admin_action'] = 'add_university'
    context.user_data['university_step'] = 'name'
    await update.callback_query.message.edit_text("Введите название университета:")

@error_handler
async def process_university_input(update, context):
    """Process step-by-step university input with validation"""
    step = context.user_data.get('university_step', 'name')
    
    if step == 'name':
        name = update.message.text
        if not validate_text(name, min_length=2):
            raise ValidationError("Название университета должно содержать минимум 2 символа")
        
        context.user_data['university_name'] = name
        context.user_data['university_step'] = 'instagram'
        await update.message.reply_text("Теперь введите ссылку на Instagram студенческой организации:")
    
    elif step == 'instagram':
        instagram = update.message.text
        if not validate_url(instagram):
            raise ValidationError("Некорректная ссылка. Должна начинаться с http://, https://, @ или t.me/")
        
        name = context.user_data['university_name']
        info = f"{name}\n{instagram}"
        
        try:
            db.add_bot_info('university_info', info)
            logger.info(f"Added new university: {name}")
            await update.message.reply_text(f"Университет '{name}' успешно добавлен!")
        finally:
            # Clear temporary data
            for key in ['university_step', 'university_name', 'pending_admin_action']:
                context.user_data.pop(key, None)

@error_handler
async def delete_handler(update, context):
    data = db.fetch_db()
    rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'university']
    if not rows:
        await update.callback_query.message.edit_text("Нет университетов для удаления.")
        return
    uni_buttons = []
    delete_map = {}
    for idx, entry in enumerate(rows):
        key = str(idx)
        delete_map[key] = entry["info"]
        uni_name = entry["info"].split(";")[0]
        uni_buttons.append([InlineKeyboardButton(uni_name, callback_data=f'delete_university_{key}')])
    context.user_data['delete_universities'] = delete_map
    uni_buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_university')])
    reply_markup = InlineKeyboardMarkup(uni_buttons)
    await update.callback_query.message.edit_text("Выберите университет для удаления:", reply_markup=reply_markup)

@error_handler
async def confirm_delete_handler(update, context, replies):
    # Use "delete_universities" as the user_data key and "university" as the category.
    await confirm_deletion_handler(update, context, 'delete_universities', 'university', replies["back_to_admin_menu"])
