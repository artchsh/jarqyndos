from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import db
from utils import error_handler, validate_admin_action, ValidationError, validate_text, validate_url, validate_price, logger

@error_handler
@validate_admin_action
async def admin_menu(update, context, replies):
    """Display psychologist administration menu"""
    logger.info(f"User {update.effective_user.id} accessed psychologist admin menu")
    await update.callback_query.message.edit_text(
        "Психологи — выберите действие:", 
        reply_markup=replies["psychologist_menu"]
    )
    context.user_data["current_category"] = "psychologist"

async def add_handler(update, context):
    context.user_data['pending_admin_action'] = 'add_psychologist'
    context.user_data['psychologist_step'] = 'name'
    await update.callback_query.message.edit_text("Введите имя и фамилию психолога:")

@error_handler
async def process_psychologist_input(update, context):
    """Process step-by-step psychologist input with validation"""
    step = context.user_data.get('psychologist_step', 'name')
    
    if step == 'name':
        name = update.message.text
        if not validate_text(name, min_length=5):
            raise ValidationError("Имя и фамилия должны содержать минимум 5 символов")
        context.user_data['psychologist_name'] = name
        context.user_data['psychologist_step'] = 'specialty'
        await update.message.reply_text("Введите специализацию психолога:")
    
    elif step == 'specialty':
        specialty = update.message.text
        if not validate_text(specialty, min_length=5):
            raise ValidationError("Специализация должна содержать минимум 5 символов")
        context.user_data['psychologist_specialty'] = specialty
        context.user_data['psychologist_step'] = 'instagram'
        await update.message.reply_text("Введите Instagram психолога:")
    
    elif step == 'instagram':
        instagram = update.message.text
        if not validate_url(instagram):
            raise ValidationError("Некорректная ссылка. Должна начинаться с @ или https://")
        context.user_data['psychologist_instagram'] = instagram
        context.user_data['psychologist_step'] = 'price'
        await update.message.reply_text("Введите стоимость сессии (если нет цены, введите 0):")
    
    elif step == 'price':
        if not validate_price(update.message.text):
            await update.message.reply_text("Пожалуйста, введите корректное число для цены:")
            return
            
        try:
            # Format and save psychologist info
            price = int(update.message.text)
            price_text = f"{price} тг." if price > 0 else "Цена не указана"
            
            info = (
                f"{context.user_data['psychologist_name']}\n"
                f"Специализация: {context.user_data['psychologist_specialty']}\n"
                f"Instagram: {context.user_data['psychologist_instagram']}\n"
                f"Стоимость: {price_text}"
            )
            
            db.add_bot_info('find_psychologist', info)
            logger.info(f"Added new psychologist: {context.user_data['psychologist_name']}")
            await update.message.reply_text("Психолог успешно добавлен!")
        finally:
            # Clear temporary data
            for key in ['psychologist_step', 'psychologist_name', 
                       'psychologist_specialty', 'psychologist_instagram']:
                context.user_data.pop(key, None)
            context.user_data.pop('pending_admin_action', None)

@error_handler
async def delete_handler(update, context):
    data = db.fetch_db()
    rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'psychologist']
    if not rows:
        await update.callback_query.message.edit_text("Нет психологов для удаления.")
        return

    buttons = []
    delete_map = {}
    for idx, entry in enumerate(rows):
        key = str(idx)
        delete_map[key] = entry["info"]
        buttons.append([InlineKeyboardButton(entry["info"], callback_data=f'delete_psychologist_{key}')])
    context.user_data['delete_psychologist'] = delete_map
    buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_psychologist')])
    await update.callback_query.message.edit_text(
        "Выберите психолога для удаления:", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@error_handler
async def confirm_delete_handler(update, context, replies):
    key = update.callback_query.data.split('_')[-1]
    info = context.user_data.get('delete_psychologist', {}).get(key)
    if info and db.delete_bot_info('psychologist', info):
        await update.callback_query.message.edit_text("Психолог удалён.")
    else:
        await update.callback_query.message.edit_text("Ошибка при удалении.")
    context.user_data.pop('pending_delete_psychologist', None)
    context.user_data.pop('delete_psychologist', None)
    await update.callback_query.message.reply_text(
        "Выберите другое действие или вернитесь:", 
        reply_markup=replies["psychologist_menu"]
    )
