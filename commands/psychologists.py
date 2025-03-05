import db
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from logger import logger
from config import FIND_PSYCHOLOGIST, MAIN_MENU
from language import textjson
from commands.system import back_button, go_back

def format_price(price) -> str:
    try:
        num = int(price)
    except (ValueError, TypeError):
        logger.debug(f"Invalid price format: {price}")
        return textjson.psychologists.price_unknown
    if num == 0:
        return textjson.psychologists.price_unknown
    str_price = "{:,}".format(num).replace(",", " ") + "₸"
    return str_price

async def handle_find_psychologist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text if update.message else None
        logger.info(f"User {update.effective_chat.id} searching for psychologists, text: {text}")
        
        # Handle back button
        if text == textjson.common.back_button or text == "Назад":
            return await go_back(update, context)
        elif text == textjson.common.main_menu_button:
            from commands.system import return_to_main_menu
            return await return_to_main_menu(update, context)
        
        # Store current state in navigation stack to enable going back
        if not context.user_data.get('nav_stack'):
            context.user_data['nav_stack'] = []
        
        # Only add MAIN_MENU to stack if we're coming from there and it's not already in stack
        if not context.user_data['nav_stack'] or context.user_data['nav_stack'][-1] != MAIN_MENU:
            context.user_data['nav_stack'].append(MAIN_MENU)
        
        psychologists = db.get_psychologists()
        logger.debug(f"Retrieved {len(psychologists) if psychologists else 0} psychologists")
        
        if not psychologists:
            await update.message.reply_text(textjson.psychologists.no_info, reply_markup=back_button)
            return FIND_PSYCHOLOGIST
        
        response = ""
        for psychologist in psychologists:
            instagram_link = psychologist.get("instagram", "")
            if instagram_link.startswith('@'):
                instagram_link = instagram_link[1:]
            instagram_link = f"https://instagram.com/{instagram_link}"
            
            if psychologist.get("price", 0) == 0:
                psychologist["price"] = textjson.psychologists.price_unknown
                
            response += f"<strong>{psychologist.get('name', '')}{textjson.psychologists.title_suffix}</strong>\r\n"
            response += f"{textjson.psychologists.specialty.format(specialty=psychologist.get('specialty', ''))}\r\n"
            response += f"{textjson.psychologists.price.format(price=format_price(psychologist.get('price')))}\r\n"
            
            # Fix the string formatting
            phone = psychologist.get("contacts", {}).get("phone", "")
            response += f"{textjson.psychologists.phone.format(phone=f'<a href=\"tel:{phone}\">{phone}</a>')}\r\n"
            response += f"<a href='{instagram_link}'>Instagram 📱</a>\n\n"
        
        await update.message.reply_text(response, reply_markup=back_button, parse_mode=ParseMode.HTML, link_preview_options={"is_disabled": True})
        return FIND_PSYCHOLOGIST
    except Exception as e:
        logger.error(f"Error in handle_find_psychologist: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return FIND_PSYCHOLOGIST
