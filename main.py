from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os, db, nest_asyncio, asyncio
from dotenv import load_dotenv
from db import escape_markdown
from categories import university, psychologist, practices, contacts
import admin
from admin import handle_admin_callback, send_announcement, handle_admin_message

load_dotenv()
TOKEN = os.getenv("TOKEN")

def get_admin_ids():
    return db.get_admin_ids()

# New: common reply keyboards.
replies = {
    "start_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Найти психолога", callback_data='find_psychologist')],
        [InlineKeyboardButton("Практики", callback_data='practices')],
        [InlineKeyboardButton("Jarqyn в твоем университете", callback_data='university_info')],
        [InlineKeyboardButton("Контакты", callback_data='contacts')],
        [InlineKeyboardButton("Сообщить об ошибке", callback_data='report_issue')]
    ]),
    "admin_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Университеты", callback_data='admin_category_university')],
        [InlineKeyboardButton("Психологи", callback_data='admin_category_psychologist')],
        [InlineKeyboardButton("Практики", callback_data='admin_category_practices')],
        [InlineKeyboardButton("Контакты", callback_data='admin_category_contacts')],
        [InlineKeyboardButton("Отправить объявление", callback_data='send_announcement')],
        [InlineKeyboardButton("Назад в меню", callback_data='back_to_menu')]
    ]),
    "back_button": InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_menu")]]),
    "university_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить университет", callback_data='add_university')],
        [InlineKeyboardButton("Удалить университет", callback_data='delete_university')],
        [InlineKeyboardButton("Назад", callback_data='admin_panel')]
    ]),
    "psychologist_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить психолога", callback_data='add_psychologist')],
        [InlineKeyboardButton("Удалить психолога", callback_data='delete_psychologist')],
        [InlineKeyboardButton("Назад", callback_data='admin_panel')]
    ]),
    "practices_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить практику", callback_data='add_practices')],
        [InlineKeyboardButton("Удалить практику", callback_data='delete_practices')],
        [InlineKeyboardButton("Назад", callback_data='admin_panel')]
    ]),
    "contacts_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить контакт", callback_data='add_contacts')],
        [InlineKeyboardButton("Удалить контакт", callback_data='delete_contacts')],
        [InlineKeyboardButton("Назад", callback_data='admin_panel')]
    ])
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Register user in JSON database
    db.add_user(update.message.chat_id)
    admin_ids = get_admin_ids()  # Get fresh list of admin IDs
    
    keyboard = [
        [InlineKeyboardButton("Найти психолога", callback_data='find_psychologist')],
        [InlineKeyboardButton("Практики", callback_data='practices')],
        [InlineKeyboardButton("Jarqyn в твоем университете", callback_data='university_info')],
        [InlineKeyboardButton("Контакты", callback_data='contacts')],
        [InlineKeyboardButton("Сообщить об ошибке", callback_data='report_issue')]
    ]
    if update.message.chat_id in admin_ids:  # Check against dynamic admin list
        keyboard.append([InlineKeyboardButton("Админ панель", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"{escape_markdown('Привет, меня зовут Dos!')}\n"
        f"{escape_markdown('Я друг проекта психологической поддержки Jarqyn.')}\n"
        f"{escape_markdown('Я помогу справиться с тревогой, стрессом, выгоранием.')}\n"
        f"{escape_markdown('Выберите действие:')}", 
        reply_markup=reply_markup, 
        parse_mode="MarkdownV2")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Handle admin callbacks
    if query.data.startswith(('admin_', 'add_', 'delete_')):
        return await handle_admin_callback(update, context)
    
    # Handle user callbacks
    if query.data in ['find_psychologist', 'practices', 'university_info', 'contacts']:
        response = db.get_bot_info()[query.data]
        back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_menu")]])
        await query.message.edit_text(response, reply_markup=back_markup, parse_mode="MarkdownV2")
        return
    
    elif query.data == 'report_issue':
        response = "Опишите вашу проблему, и мы постараемся её решить. Отправьте сообщение в чат."
        back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_menu")]])
        await query.message.edit_text(response, reply_markup=back_markup)
        return

    elif query.data == 'back_to_menu':
        admin_ids = get_admin_ids()  # Get fresh list of admin IDs
        keyboard = [
            [InlineKeyboardButton("Найти психолога", callback_data='find_psychologist')],
            [InlineKeyboardButton("Практики", callback_data='practices')],
            [InlineKeyboardButton("Jarqyn в твоем университете", callback_data='university_info')],
            [InlineKeyboardButton("Контакты", callback_data='contacts')],
            [InlineKeyboardButton("Сообщить об ошибке", callback_data='report_issue')]
        ]
        if query.message.chat.id in admin_ids:  # Check against dynamic admin list
            keyboard.append([InlineKeyboardButton("Админ панель", callback_data='admin_panel')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "Привет, меня зовут Dos!\n"
            "Я друг проекта психологической поддержки Jarqyn.\n"
            "Я помогу справиться с тревогой, стрессом, выгоранием.\n"
            "Выберите действие:", reply_markup=reply_markup)
        return

    elif query.data in ['admin_announce']:
        instructions = {"admin_announce": "Чтобы отправить объявление, используйте команду /announce ..."}
        response = instructions.get(query.data, "")
    
    elif query.data == 'practices':
        # Fetch all practices from database
        data = db.fetch_db()
        practices_data = [entry for entry in data.get("bot_info", []) if entry["category"] == 'practices']
        
        if not practices_data:
            back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_menu")]])
            await query.message.edit_text("Нет доступных практик.", reply_markup=back_markup)
            return

        # Create buttons for each practice
        buttons = []
        for practice in practices_data:
            practice_info = practice["info"]
            if isinstance(practice_info, dict):  # New format
                title = practice_info["title"]
                buttons.append([InlineKeyboardButton(title, callback_data=f'show_practice_{practice["id"]}')])
        
        # Add back button
        buttons.append([InlineKeyboardButton("Назад", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await query.message.edit_text("Выберите практику:", reply_markup=reply_markup)
        return

    elif query.data.startswith('show_practice_'):
        practice_id = int(query.data.split('_')[-1])
        data = db.fetch_db()
        practice = next((p for p in data.get("bot_info", []) 
                        if p["category"] == 'practices' and p["id"] == practice_id), None)
        
        if practice and isinstance(practice["info"], dict):
            content = practice["info"]["content"]
            back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="practices")]])
            await query.message.edit_text(content, reply_markup=back_markup)
        else:
            await query.message.edit_text("Практика не найдена.")
        return

    else:
        response = "Неизвестная команда."
    await query.message.edit_text(response)

async def receive_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from users and admin actions"""
    # Handle admin actions if applicable
    if update.message.chat_id in get_admin_ids():
        if await handle_admin_message(update, context):
            return
            
    # Handle user issue reports
    await update.message.reply_text("Спасибо! Мы рассмотрим вашу проблему.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # First register admin handlers (including conversation handlers)
    admin.register_admin_handlers(app)
    
    # Then register other handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("announce", send_announcement))
    
    # General callback handler should be last to not interfere with conversation handlers
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_issue))
    
    app.run_polling()

if __name__ == '__main__':
    main()
