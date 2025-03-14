import db
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from logger import logger
from config import PRACTICES_MENU, PRACTICE_CATEGORY, PRACTICE_DETAIL, MAIN_MENU
from language import textjson
from commands.system import back_button, go_back

async def handle_practices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"User {update.effective_chat.id} accessing practices")
        
        # Store current state in navigation stack to enable going back
        if not context.user_data.get('nav_stack'):
            context.user_data['nav_stack'] = []
        
        # Only add MAIN_MENU to stack if we're coming from there and it's not already in stack
        if not context.user_data['nav_stack'] or context.user_data['nav_stack'][-1] != MAIN_MENU:
            context.user_data['nav_stack'].append(MAIN_MENU)
            
        categories = db.get_practice_categories()
        logger.debug(f"Retrieved {len(categories) if categories else 0} practice categories")
        
        if not categories:
            await update.message.reply_text(textjson.practices.no_info, reply_markup=back_button)
            return PRACTICES_MENU
        
        keyboard = []
        logger.info(f"Categories: {categories}")
        for category in categories:
            keyboard.append([category + textjson.practices.category_suffix])
        keyboard.append([textjson.common.back_button])
        keyboard.append([textjson.common.main_menu_button])
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Store categories for later use
        context.user_data['practice_categories'] = categories
        
        await update.message.reply_text(textjson.practices.select_category, reply_markup=markup)
        return PRACTICES_MENU
    except Exception as e:
        logger.error(f"Error in handle_practices: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return PRACTICES_MENU

async def practices_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        logger.info(f"User {update.effective_chat.id} selected in practices menu: {text}")
        
        if text == textjson.common.back_button or text == "Назад":
            return await go_back(update, context)
        elif text == textjson.common.main_menu_button:
            from commands.system import return_to_main_menu
            return await return_to_main_menu(update, context)
        
        # Remove emoji if present
        text = text.split(textjson.practices.category_suffix)[0] if textjson.practices.category_suffix in text else text
        
        categories = context.user_data.get('practice_categories', [])
        if text not in categories:
            logger.warning(f"Practice category not found: {text}")
            await update.message.reply_text(textjson.common.fallback, reply_markup=back_button)
            return PRACTICES_MENU
        
        # Store the previous state and category
        if not context.user_data.get('nav_stack'):
            context.user_data['nav_stack'] = []
        context.user_data['nav_stack'].append(PRACTICES_MENU)
        return await show_practice_category(update, context, text)
    except Exception as e:
        logger.error(f"Error in practices_menu_handler: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return PRACTICES_MENU

async def show_practice_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category=None):
    try:
        if not category:
            category = context.user_data.get('current_category')
            if not category:
                logger.warning(f"No category found for user {update.effective_chat.id}")
                await update.message.reply_text(textjson.common.unknown_state, reply_markup=back_button)
                return PRACTICE_CATEGORY
        
        logger.info(f"User {update.effective_chat.id} viewing category: {category}")
        practices_data = db.get_practices_by_category(category)
        logger.debug(f"Retrieved {len(practices_data) if practices_data else 0} practices for category {category}")
        
        if not practices_data:
            await update.message.reply_text(textjson.practices.no_practices.format(category=category), reply_markup=back_button)
            return PRACTICE_CATEGORY
        
        buttons = []
        row = []
        response = textjson.practices.category_header.format(category=category)
        for index, practice in enumerate(practices_data, start=1):
            title = practice.get("name", "")
            description = practice.get('description', '')
            response += f"{index}. <strong>{title}</strong>\n"
            response += f"{(description + '\n') if description else ''}"
            
            button = InlineKeyboardButton(str(index), callback_data=f"show_practice_{practice.get('id')}")
            row.append(button)
            
            if len(row) == 2:
                buttons.append(row)
                row = []
        
        if row:
            buttons.append(row)
        
        inline_markup = InlineKeyboardMarkup(buttons)
        context.user_data['current_category'] = category
        
        response += textjson.practices.select_practice
        await update.message.reply_text(response, reply_markup=inline_markup, parse_mode=ParseMode.HTML)
        
        # Send a message with the back button after the inline keyboard message
        await update.message.reply_text(textjson.common.navigation_hint, reply_markup=back_button)
        return PRACTICE_CATEGORY
    except Exception as e:
        logger.error(f"Error in show_practice_category: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return PRACTICE_CATEGORY

async def show_practice_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Helper function to show practice details when coming back to a practice"""
    try:
        practice_id = context.user_data.get('current_practice_id')
        if not practice_id:
            logger.warning(f"No practice ID found for user {update.effective_chat.id}")
            await update.message.reply_text(textjson.common.unknown_state, reply_markup=back_button)
            return PRACTICE_CATEGORY
            
        practices_data = db.get_practices()
        practice = next((p for p in practices_data if p.get("id") == practice_id), None)
        
        if not practice:
            logger.warning(f"Practice not found with ID: {practice_id}")
            await update.message.reply_text(textjson.practices.practice_not_found, reply_markup=back_button)
            return PRACTICE_CATEGORY
            
        name = practice.get("name", "")
        name = f"<strong>{name}{textjson.practices.category_suffix}</strong>\n\n"
        content = name + practice.get("content", "")
        if practice.get("author"):
            content += f"\n\n{textjson.practices.author.format(author=practice.get('author'))}"
            
        await update.message.reply_text(content, reply_markup=back_button, parse_mode=ParseMode.HTML)
        
        # NEW: if practice has an audio url, send the audio and store its message id
        if practice.get("audio") and practice["audio"].get("url"):
            audio_message = await update.message.reply_audio(audio=practice["audio"]["url"])
            context.user_data["practice_audio_message_id"] = audio_message.message_id

        return PRACTICE_DETAIL
    except Exception as e:
        logger.error(f"Error showing practice detail: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return PRACTICE_CATEGORY

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data
        
        logger.info(f"User {update.effective_chat.id} clicked button: {data}")
        
        if data.startswith('show_practice_'):
            try:
                practice_id = int(data.split('_')[-1])
                logger.debug(f"Showing practice with ID: {practice_id}")
            except ValueError:
                logger.error(f"Invalid practice ID format: {data}")
                await query.edit_message_text(text=textjson.practices.practice_error)
                return PRACTICE_CATEGORY
            
            practices_data = db.get_practices()
            practice = next(
                (p for p in practices_data if p.get("id") == practice_id),
                None
            )
            
            if practice:
                name = practice.get("name", "")
                name = f"<strong>{name}{textjson.practices.category_suffix}</strong>\n\n"
                content = name + practice.get("content", "")
                if practice.get("author"):
                    content += f"\n\n{textjson.practices.author.format(author=practice.get('author'))}"
                
                # Push current state to navigation stack
                if not context.user_data.get('nav_stack'):
                    context.user_data['nav_stack'] = []
                context.user_data['nav_stack'].append(PRACTICE_CATEGORY)
                context.user_data['current_practice_id'] = practice_id
                
                await query.edit_message_text(text=content, parse_mode=ParseMode.HTML)
                
                # NEW: if practice has an audio url, send the audio and store its message id
                if practice.get("audio") and practice["audio"].get("url"):
                    audio_message = await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=practice["audio"]["url"]
                    )
                    context.user_data["practice_audio_message_id"] = audio_message.message_id

                # Send a new message with back button
                # await context.bot.send_message(
                #     chat_id=update.effective_chat.id,
                #     text=textjson.common.navigation_hint,
                #     reply_markup=back_button
                # )
                return PRACTICE_DETAIL
            else:
                logger.warning(f"Practice not found with ID: {practice_id}")
                await query.edit_message_text(text=textjson.practices.practice_not_found)
                return PRACTICE_CATEGORY
    except Exception as e:
        logger.error(f"Error in button_handler: {str(e)}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=textjson.practices.practice_error,
                reply_markup=back_button
            )
        except Exception:
            pass  # Suppress any errors while trying to notify the user
        return PRACTICE_CATEGORY

async def practice_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        logger.info(f"User {update.effective_chat.id} in practice detail: {text}")
        
        if text == textjson.common.back_button or text == "Назад":
            return await go_back(update, context)
        elif text == textjson.common.main_menu_button:
            from commands.system import return_to_main_menu
            return await return_to_main_menu(update, context)
        
        await update.message.reply_text(textjson.common.navigation_hint, reply_markup=back_button)
        return PRACTICE_DETAIL
    except Exception as e:
        logger.error(f"Error in practice_detail_handler: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return PRACTICE_DETAIL
