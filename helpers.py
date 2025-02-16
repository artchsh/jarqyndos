from telegram import InlineKeyboardMarkup
import db
from utils import logger

async def confirm_deletion_handler(update, context, delete_map_key: str, category: str, menu_reply):
    """
    Common deletion confirmation handler.
    delete_map_key: key in context.user_data holding the deletion mapping.
    category: category string to use when deleting (should match db entry).
    menu_reply: reply_markup for returning to the menu.
    """
    key = update.callback_query.data.split('_')[-1]
    delete_map = context.user_data.get(delete_map_key, {})
    info = delete_map.get(key)
    if info and db.delete_bot_info(category, info):
        await update.callback_query.message.edit_text(f"{category.capitalize()} удалён.")
    else:
        await update.callback_query.message.edit_text("Ошибка при удалении.")
    context.user_data.pop(f'pending_delete_{category}', None)
    context.user_data.pop(delete_map_key, None)
    await update.callback_query.message.reply_text("Выберите другое действие или вернитесь:", reply_markup=menu_reply)
