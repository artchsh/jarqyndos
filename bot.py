import db, os
from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Define common inline keyboards
start_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Найти психолога", callback_data='find_psychologist')],
    [InlineKeyboardButton(text="Практики", callback_data='practices')],
    [InlineKeyboardButton(text="Jarqyn в твоем университете", callback_data='university_info')],
    [InlineKeyboardButton(text="Контакты", callback_data='contacts')],
    [InlineKeyboardButton(text="Сообщить об ошибке", callback_data='report_issue')]
])

back_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.add_user(update.effective_chat.id)
    text = (
        f"{'Привет, меня зовут Dos!'}\n"
        f"{'Я друг проекта психологической поддержки Jarqyn.'}\n"
        f"{'Я помогу справиться с тревогой, стрессом, выгоранием.'}\n"
        f"{'Выберите действие:'}"
    )
    await update.message.reply_text(text, reply_markup=start_menu)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'university_info':
        universities = db.get_universities()
        if not universities:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
            ])
            await query.edit_message_text(text="Нет информации о университетах.", reply_markup=markup)
            return
        response = ""
        for university in universities:
            instagram_link = university['instagram']
            if instagram_link.startswith('@'):
                instagram_link = instagram_link[1:]
            instagram_link = f"https://instagram.com/{instagram_link}"
            response += f"<strong>{university['name']}</strong>\r\n"
            response += f"<a href='{instagram_link}'>{university['instagram']}</a>\n\n"
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
        ])
        await query.edit_message_text(text=response, reply_markup=markup, parse_mode=ParseMode.HTML)
        
    elif data == 'find_psychologist':
        psychologists = db.get_psychologists()
        if not psychologists:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
            ])
            await query.edit_message_text(text="Нет информации о психологах.", reply_markup=markup)
            return
        
        response = ""
        for psychologist in psychologists:
            instagram_link = psychologist.get("instagram", "")
            if instagram_link.startswith('@'):
                instagram_link = instagram_link[1:]
            instagram_link = f"https://instagram.com/{instagram_link}"
            
            if psychologist.get("price", 0) == 0:
                psychologist["price"] = "Уточнить"
            response += f"<strong>{psychologist.get("name", "")}</strong>\r\n"
            response += f"Специализация: {psychologist.get("specialty", "")}\r\n"
            response += f"Цена: {psychologist.get("price")}\r\n"
            response += f"Телефон: <a href='tel:{psychologist['contacts']['phone']}'>{psychologist['contacts']['phone']}</a>\r\n"
            response += f"<a href='{instagram_link}'>Instagram</a>\n\n"
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
        ])
        await query.edit_message_text(text=response, reply_markup=markup, parse_mode=ParseMode.HTML)
        
    elif data == 'contacts':
        contacts = db.get_contacts()
        if not contacts:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
            ])
            await query.edit_message_text(text="Нет контактной информации.", reply_markup=markup)
            return
        response = ""
        for contact in contacts:
            response += f"<strong>{contact.get('name', '')}</strong>\r\n"
            response += f"Телефон: {contact.get('phone', '')}\r\n"
            response += f"Email: {contact.get('email', '')}\n\n"
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
        ])
        await query.edit_message_text(text=response, reply_markup=markup, parse_mode=ParseMode.HTML)

    elif data == 'report_issue':
        response = "Опишите вашу проблему, и мы постараемся её решить. Отправьте сообщение в чат."
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
        ])
        await query.edit_message_text(text=response, reply_markup=markup)

    elif data == 'back_to_menu':
        text = (
            "Привет, меня зовут Dos!\n"
            "Я друг проекта психологической поддержки Jarqyn.\n"
            "Я помогу справиться с тревогой, стрессом, выгоранием.\n"
            "Выберите действие:"
        )
        await query.edit_message_text(text=text, reply_markup=start_menu)

    elif data == 'practices':
        practices_data = db.get_practices()
        if not practices_data:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
            ])
            await query.edit_message_text(text="Нет доступных практик.", reply_markup=markup)
            return

        buttons = []
        for practice in practices_data:
            title = practice.get("name", "")
            buttons.append([InlineKeyboardButton(title, callback_data=f"show_practice_{practice.get('id')}")])
        buttons.append([InlineKeyboardButton("Назад", callback_data="back_to_menu")])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await query.edit_message_text(text="Выберите практику:", reply_markup=markup)

    elif data.startswith('show_practice_'):
        try:
            practice_id = int(data.split('_')[-1])
        except ValueError:
            await query.edit_message_text(text="Неверный идентификатор практики.")
            return
        practices_data = db.get_practices()
        practice = next(
            (p for p in practices_data if p.get("id") == practice_id),
            None
        )
        if practice:
            name = practice.get("name", "")
            name = f"<strong>{name}</strong>\n"
            content = name + practice.get("content", "")
            if practice.get("author"):
                content += f"\n\nАвтор: {practice.get('author')}"
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Назад", callback_data="practices")]
            ])
            await query.edit_message_text(text=content, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text="Практика не найдена.")

    else:
        await query.edit_message_text(text="Неизвестная команда.")

async def receive_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle user issue reports
    await update.message.reply_text("Спасибо! Мы рассмотрим вашу проблему.")

def main():
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_issue))

    # Start the bot (this will run until interrupted)
    application.run_polling(poll_interval=2)

if __name__ == '__main__':
    main()
