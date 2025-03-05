import db
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from logger import logger
from config import CONTACTS_MENU, MAIN_MENU
from language import textjson
from commands.system import back_button

async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"User {update.effective_chat.id} viewing contacts")
        contacts = db.get_contacts()
        logger.debug(f"Retrieved {len(contacts) if contacts else 0} contacts")
        
        # Store current state in navigation stack to enable going back
        if not context.user_data.get('nav_stack'):
            context.user_data['nav_stack'] = []
        
        # Only add MAIN_MENU to stack if we're coming from there and it's not already in stack
        if not context.user_data['nav_stack'] or context.user_data['nav_stack'][-1] != MAIN_MENU:
            context.user_data['nav_stack'].append(MAIN_MENU)
        
        if not contacts:
            await update.message.reply_text(textjson.contacts.no_info, reply_markup=back_button)
            return CONTACTS_MENU
        
        response = textjson.contacts.header
        for contact in contacts:
            response += f"<strong>{contact.get('name', '')}</strong>\r\n"
            response += f"{textjson.contacts.phone.format(phone=f'<a href=\"tel:{contact.get("phone")}\">{contact.get("phone")}</a>')}\r\n"
            response += f"{textjson.contacts.email.format(email=f'<a href=\"mailto:{contact.get("email")}\">{contact.get("email")}</a>')}\n\n"
        
        await update.message.reply_text(response, reply_markup=back_button, parse_mode=ParseMode.HTML, link_preview_options={"is_disabled": True})
        return CONTACTS_MENU
    except Exception as e:
        logger.error(f"Error in handle_contacts: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return CONTACTS_MENU