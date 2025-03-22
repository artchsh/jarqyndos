import db
import traceback
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import TimedOut, NetworkError, RetryAfter, BadRequest

from logger import logger
from config import last_practice_ids, MAIN_MENU, UNIVERSITY_MENU, FIND_PSYCHOLOGIST, PRACTICES_MENU,PRACTICE_CATEGORY, PRACTICE_DETAIL, CONTACTS_MENU, REPORT_ISSUE, PARTNERS_MENU
from language import textjson


# Main keyboards
start_menu = ReplyKeyboardMarkup([
    [textjson.main_menu.university],
    [textjson.main_menu.psychologist],
    [textjson.main_menu.practices],
    [textjson.main_menu.contacts],
    [textjson.main_menu.partners],
    [textjson.main_menu.report_issue]
], resize_keyboard=True)

back_button = ReplyKeyboardMarkup([
    [textjson.common.back_button], 
    [textjson.common.main_menu_button]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_chat.id} started the bot")
    try:
        db.add_user(update.effective_chat.id)
        # Store an empty navigation stack in user_data
        context.user_data['nav_stack'] = []
        
        # Get the start text from the database
        text = db.get_start_text()
        logger.debug(f"Retrieved start text: {text[:20]}...")
            
        await update.message.reply_text(text, reply_markup=start_menu)
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic)
        return ConversationHandler.END

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from the main menu"""
    try:
        text = update.message.text.split(" ")[0]  # Remove emoji if present
        logger.info(f"User {update.effective_chat.id} selected from main menu: {text}")
        
        # Reset navigation stack when at main menu
        context.user_data['nav_stack'] = []
        
        if text == "Узнать":
            # Import here to avoid circular imports
            from commands.universities import handle_university_info
            context.user_data['nav_stack'].append(MAIN_MENU)
            return await handle_university_info(update, context)
        elif text == "Найти":
            from commands.psychologists import handle_find_psychologist
            context.user_data['nav_stack'].append(MAIN_MENU)
            return await handle_find_psychologist(update, context)
        elif text == "Практики":
            from commands.practices import handle_practices
            context.user_data['nav_stack'].append(MAIN_MENU)
            return await handle_practices(update, context)
        elif text == "Контакты":
            from commands.contacts import handle_contacts
            context.user_data['nav_stack'].append(MAIN_MENU)
            return await handle_contacts(update, context)
        elif text == "Наши":
            from commands.partners import handle_partners
            context.user_data['nav_stack'].append(MAIN_MENU)
            return await handle_partners(update, context)
        elif text == "Сообщить":
            context.user_data['nav_stack'].append(MAIN_MENU)
            await update.message.reply_text(
                textjson.report_issue.prompt,
                reply_markup=back_button
            )
            return REPORT_ISSUE
        else:
            logger.warning(f"User {update.effective_chat.id} sent unexpected text: {text}")
            await update.message.reply_text(textjson.common.select_option, reply_markup=start_menu)
            return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in main menu handler: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=start_menu)
        return MAIN_MENU

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle going back to the previous state"""
    try:
        logger.info(f"User {update.effective_chat.id} requested to go back")
        
        # NEW: Delete practice audio message if it exists
        if "practice_audio_message_id" in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data["practice_audio_message_id"]
                )
            except Exception:
                pass  # Ignore deletion errors
            context.user_data.pop("practice_audio_message_id", None)
        
        nav_stack = context.user_data.get('nav_stack', [])
        logger.debug(f"Navigation stack: {nav_stack}")
        
        if not nav_stack:
            # If stack is empty, go to main menu
            text = db.get_start_text()
            await update.message.reply_text(text, reply_markup=start_menu)
            return MAIN_MENU
        
        # Pop the last state from stack
        prev_state = nav_stack.pop()
        logger.debug(f"Going back to state: {prev_state}")
        
        # Navigate to previous state
        if prev_state == MAIN_MENU:
            await update.message.reply_text(textjson.common.go_to_main_menu, reply_markup=start_menu)
            return MAIN_MENU
        elif prev_state == UNIVERSITY_MENU:
            from commands.universities import handle_university_info
            return await handle_university_info(update, context)
        elif prev_state == PRACTICES_MENU:
            from commands.practices import handle_practices
            return await handle_practices(update, context)
        elif prev_state == PRACTICE_CATEGORY:
            from commands.practices import show_practice_category
            # Get the category from user_data and return to that category
            category = context.user_data.get('current_category')
            if category:
                return await show_practice_category(update, context, category)
            else:
                from commands.practices import handle_practices
                return await handle_practices(update, context)
        elif prev_state == FIND_PSYCHOLOGIST:
            from commands.psychologists import handle_find_psychologist
            return await handle_find_psychologist(update, context)
        elif prev_state == PRACTICE_DETAIL:
            from commands.practices import show_practice_detail
            return await show_practice_detail(update, context)
        elif prev_state == CONTACTS_MENU:
            from commands.contacts import handle_contacts
            return await handle_contacts(update, context)
        elif prev_state == PARTNERS_MENU:
            from commands.partners import handle_partners
            return await handle_partners(update, context)
        else:
            # Default to main menu if state is unknown
            logger.warning(f"Unknown previous state: {prev_state}, defaulting to main menu")
            await update.message.reply_text(textjson.common.unknown_state, reply_markup=start_menu)
            return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in go_back handler: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=start_menu)
        return MAIN_MENU

async def return_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle returning to the main menu from anywhere"""
    try:
        logger.info(f"User {update.effective_chat.id} returning to main menu")
        
        # Clear navigation stack
        context.user_data['nav_stack'] = []
        
        await update.message.reply_text(textjson.common.go_to_main_menu, reply_markup=start_menu)
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in return_to_main_menu handler: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=start_menu)
        return MAIN_MENU

async def report_issue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        logger.info(f"User {update.effective_chat.id} in report issue: {text}")
        
        if text == textjson.common.back_button or text == "Назад":
            return await go_back(update, context)
        elif text == textjson.common.main_menu_button:
            return await return_to_main_menu(update, context)
        
        # Handle user issue reports
        admin_ids = db.get_admin_ids()
        if not admin_ids:
            logger.error("No admin IDs found in database")
            await update.message.reply_text(textjson.report_issue.send_error, reply_markup=back_button)
            return REPORT_ISSUE
        
        for admin_id in admin_ids:
            message = textjson.report_issue.admin_message.format(user_id=update.effective_chat.id, text=update.message.text)
            try:
                await context.bot.send_message(admin_id, message)
                logger.info(f"Issue report sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to send report to admin {admin_id}: {str(e)}")
        
        await update.message.reply_text(textjson.report_issue.thanks, reply_markup=start_menu)
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in report_issue_handler: {str(e)}", exc_info=True)
        await update.message.reply_text(textjson.common.error_generic, reply_markup=back_button)
        return REPORT_ISSUE

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Fallback handler triggered by user {update.effective_chat.id}")
    await update.message.reply_text(textjson.common.fallback, reply_markup=start_menu)
    return MAIN_MENU

async def error_handler(update, context):
    """Log errors caused by Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    try:
        # Get the error details
        error_msg = str(context.error)
        tb_string = ''.join(traceback.format_exception(None, context.error, context.error.__traceback__))
        
        # Log the error to console
        logger.error(f"Update {update} caused error {error_msg}")
        logger.debug(f"Full traceback: {tb_string}")
        
        if update and update.effective_chat:
            # Let the user know an error happened
            if isinstance(context.error, (TimedOut, NetworkError)):
                message = textjson.common.network_error
            elif isinstance(context.error, RetryAfter):
                message = textjson.common.bot_overloaded.format(retry_after=context.error.retry_after)
            elif isinstance(context.error, BadRequest):
                message = textjson.common.bad_request
            else:
                message = textjson.common.error_generic
            
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=message,
                    reply_markup=start_menu
                )
            except Exception:
                # If we can't send a message, just log the error
                logger.error("Failed to send error message to user")
    except Exception as e:
        logger.error(f"Error in error handler: {str(e)}")

async def check_new_practices_job(context: ContextTypes.DEFAULT_TYPE):
    global last_practice_ids
    try:
        logger.debug("Running check_new_practices_job")
        practices = db.get_practices()
        current_ids = {practice.get("id") for practice in practices if practice.get("id") is not None}
        logger.info(f"Fetched {len(current_ids)} practices.")
        if not last_practice_ids:
            last_practice_ids = current_ids
            logger.info("Initialized practice IDs without announcement.")
            return
        new_ids = current_ids - last_practice_ids
        if new_ids:
            new_practices = [practice for practice in practices if practice.get("id") in new_ids]
            logger.info(f"Detected {len(new_practices)} new practices: {new_ids}")
            message = textjson.practices.new_practices
            buttons = []
            row = []
            for idx, practice in enumerate(new_practices, start=1):
                message += f"{idx}. <strong>{practice.get('name')}</strong>\n"
                message += f"{practice.get('description', '')}\n\n"
                button = InlineKeyboardButton(str(idx), callback_data=f"show_practice_{practice.get('id')}")
                row.append(button)
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            # Retrieve all user chat IDs
            user_ids = db.get_users()
            logger.debug(f"Sending announcements to {len(user_ids)} users")
            for user in user_ids:
                try:
                    await context.bot.send_message(chat_id=user, text=message, reply_markup=markup, parse_mode=ParseMode.HTML)
                    logger.info(f"Sent new practice announcement to user {user}.")
                except Exception as e:
                    logger.error(f"Error sending announcement to user {user}: {str(e)}")
        else:
            logger.debug("No new practices found.")
        last_practice_ids = current_ids
    except Exception as e:
        logger.error(f"Error in check_new_practices_job: {str(e)}", exc_info=True)

async def heartbeat_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Heartbeat: Bot is running. Active conversations: {len(context.application.chat_data)}")
