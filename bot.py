from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

from logger import logger
from config import TOKEN, MAIN_MENU, UNIVERSITY_MENU, FIND_PSYCHOLOGIST, PRACTICES_MENU, PRACTICE_CATEGORY, PRACTICE_DETAIL, CONTACTS_MENU, REPORT_ISSUE

# Import command handlers from modules
from commands.system import start, main_menu_handler, fallback_handler, error_handler, check_new_practices_job, heartbeat_job
from commands.system import go_back, return_to_main_menu, report_issue_handler
from commands.universities import university_menu_handler, handle_university_info
from commands.practices import practices_menu_handler, practice_detail_handler, button_handler, handle_practices
from commands.psychologists import handle_find_psychologist
from commands.contacts import handle_contacts

def main():
    # Create the application with better polling parameters
    application = Application.builder().token(TOKEN).build()
    
    logger.info("Starting bot with modular structure")
    
    # Create conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT, start),
            MessageHandler(filters.COMMAND, start)
        ],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            UNIVERSITY_MENU: [
                MessageHandler(filters.Regex("^Вернуться в главное меню 🏠$"), return_to_main_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, university_menu_handler)
            ],
            FIND_PSYCHOLOGIST: [
                MessageHandler(filters.Regex("^Вернуться в главное меню 🏠$"), return_to_main_menu),
                MessageHandler(filters.Regex("^Назад ↩️$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_find_psychologist)
            ],
            CONTACTS_MENU: [
                MessageHandler(filters.Regex("^Вернуться в главное меню 🏠$"), return_to_main_menu),
                MessageHandler(filters.Regex("^Назад ↩️$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, go_back)
            ],
            PRACTICES_MENU: [
                MessageHandler(filters.Regex("^Вернуться в главное меню 🏠$"), return_to_main_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, practices_menu_handler)
            ],
            PRACTICE_CATEGORY: [
                CallbackQueryHandler(button_handler),
                MessageHandler(filters.Regex("^Вернуться в главное меню 🏠$"), return_to_main_menu),
                MessageHandler(filters.Regex("^Назад ↩️$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, go_back)
            ],
            PRACTICE_DETAIL: [
                MessageHandler(filters.Regex("^Вернуться в главное меню 🏠$"), return_to_main_menu),
                MessageHandler(filters.Regex("^Назад ↩️$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, practice_detail_handler)
            ],
            REPORT_ISSUE: [
                MessageHandler(filters.Regex("^Вернуться в главное меню 🏠$"), return_to_main_menu),
                MessageHandler(filters.Regex("^Назад ↩️$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, report_issue_handler)
            ],
        },
        fallbacks=[CommandHandler("start", start), MessageHandler(filters.ALL, fallback_handler)],
    )
    
    application.add_handler(conv_handler)
    
    # Schedule periodic job for new practices check every 1 minute (60 seconds)
    application.job_queue.run_repeating(check_new_practices_job, interval=60, first=0)
    logger.info("Bot started and job scheduled.")
    
    # Add a heartbeat job to run every 5 minutes
    application.job_queue.run_repeating(heartbeat_job, interval=300, first=0)
    
    # Register the error handler
    application.add_error_handler(error_handler)
    
    # Start the bot (this will run until interrupted)
    application.run_polling(poll_interval=2)

if __name__ == '__main__':
    main()
