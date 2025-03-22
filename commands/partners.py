import db
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from logger import logger
from config import PARTNERS_MENU, MAIN_MENU
from language import textjson
from commands.system import back_button, go_back

async def handle_partners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text if update.message else None
        logger.info(f"User {update.effective_chat.id} viewing partners, text: {text}")
        
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
        
        partners = db.get_partners()
        logger.debug(f"Retrieved {len(partners) if partners else 0} partners")
        
        if not partners:
            await update.message.reply_text(textjson.partners.no_info, reply_markup=back_button)
            return PARTNERS_MENU
        
        response = textjson.partners.title
        for partner in partners:
            response += f"<strong>{partner.get('name', '')}</strong>\n"
            response += f"{partner.get('description', '')}\n"
            if partner.get('link'):
                response += f"<a href='{partner.get('link')}'>{textjson.partners.visit_link}</a>\n\n"
            else:
                response += "\n"
        
        await update.message.reply_text(response, reply_markup=back_button, parse_mode=ParseMode.HTML, link_preview_options={"is_disabled": True})
        return PARTNERS_MENU
    except Exception as e:
        logger.error(f"Error in handle_partners: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return PARTNERS_MENU
