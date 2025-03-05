import db
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from logger import logger
from config import UNIVERSITY_MENU, MAIN_MENU
from language import textjson
from commands.system import back_button, go_back

async def handle_university_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"User {update.effective_chat.id} accessing university info")
        universities = db.get_universities()
        logger.debug(f"Retrieved {len(universities) if universities else 0} universities")
        
        # Store current state in navigation stack to enable going back
        if not context.user_data.get('nav_stack'):
            context.user_data['nav_stack'] = []
            
        # Only add MAIN_MENU to stack if we're coming from there and it's not already in stack
        if not context.user_data['nav_stack'] or context.user_data['nav_stack'][-1] != MAIN_MENU:
            context.user_data['nav_stack'].append(MAIN_MENU)
        
        if not universities:
            await update.message.reply_text(textjson.universities.no_info, reply_markup=back_button)
            return UNIVERSITY_MENU
        
        keyboard = []
        for university in universities:
            keyboard.append([university.get("name", "") + textjson.universities.university_suffix])
        keyboard.append([textjson.common.back_button])
        keyboard.append([textjson.common.main_menu_button])
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(textjson.universities.select_prompt, reply_markup=markup)
        
        # Store universities in context for later use
        context.user_data['universities'] = universities
        return UNIVERSITY_MENU
    except Exception as e:
        logger.error(f"Error in handle_university_info: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return UNIVERSITY_MENU

async def university_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        logger.info(f"User {update.effective_chat.id} selected in university menu: {text}")
        
        if text == textjson.common.back_button or text == "Назад":
            return await go_back(update, context)
        elif text == textjson.common.main_menu_button:
            from commands.system import return_to_main_menu
            return await return_to_main_menu(update, context)
        
        # Remove emoji if present
        text = text.split(textjson.universities.university_suffix)[0] if textjson.universities.university_suffix in text else text
        
        universities = context.user_data.get('universities', [])
        university = next((u for u in universities if u.get("name") == text), None)
        
        if not university:
            logger.warning(f"University not found: {text}")
            await update.message.reply_text(textjson.universities.not_found, reply_markup=back_button)
            return UNIVERSITY_MENU
        
        university_id = university.get("id")
        logger.debug(f"Showing university ID: {university_id}")
        response = ""
        instagram_link = university['instagram']
        if instagram_link.startswith('@'):
            instagram_link = instagram_link[1:]
            instagram_link = f"https://instagram.com/{instagram_link}"
        else:
            instagram_link = f"https://instagram.com/{instagram_link}"
        
        response += f"<strong>{university['name']}{textjson.universities.university_suffix}</strong>\r\n\r\n"
        response += f"{university['description']}\r\n\r\n"
        
        if university["link"]["url"] and university["link"]["title"]:
            response += f"<a href='{university['link']['url']}'>{university['link']['title']}</a>\n\n"
        elif university["link"]["title"] and not university["link"]["url"]:
            response += f"<a href='{instagram_link}'>{university['link']['title']}</a>\n\n"
        elif university["link"]["url"] and not university["link"]["title"]:
            response += f"<a href='{university['link']['url']}'>{textjson.universities.visit_website}</a>\n\n"
        
        response += f"<a href='{instagram_link}'>Instagram 📱</a>\n\n"
        
        events = db.get_university_events(university_id)
        if events:
            logger.debug(f"Retrieved {len(events)} events for university {university_id}")
            response += textjson.universities.events_header
            for event in events:
                response += f"<strong>{event.get('title')}</strong>\n"
                response += f"{textjson.universities.event_date.format(date=event.get('date'))}\n"
                response += f"{textjson.universities.event_description.format(description=event.get('description'))}\n"
                response += f"<a href='{event.get('link')}'>{textjson.universities.event_link}</a>\n\n"
        
        await update.message.reply_text(response, reply_markup=back_button, parse_mode=ParseMode.HTML)
        return UNIVERSITY_MENU
    except Exception as e:
        logger.error(f"Error in university_menu_handler: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return UNIVERSITY_MENU
