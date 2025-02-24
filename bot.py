import db, os, logging, sys, json
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from classes import Data, Contact, Event, Psychologist, Practice, University

# Update logging configuration to log into bot.log and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# from env.json import TOKEN
with open("env.json", "r") as f:
    env = json.load(f)

TOKEN = env["TOKEN"]

start_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Узнать о JARQYN", callback_data='university_info')],
    [InlineKeyboardButton(text="Найти психолога", callback_data='find_psychologist')],
    [InlineKeyboardButton(text="Практики", callback_data='practices')],
    [InlineKeyboardButton(text="Контакты", callback_data='contacts')],
    [InlineKeyboardButton(text="Сообщить об ошибке", callback_data='report_issue')]
])

back_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
])

def format_price(price) -> str:
    try:
        num = int(price)
    except (ValueError, TypeError):
        return "Уточнить"
    if num == 0:
        return "Уточнить"
    str_price = "{:,}".format(num).replace(",", " ") + "₸"
    return str_price

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.add_user(update.effective_chat.id)
    text = (
        "Привет, я - DOS\n"
        "Друг проекта JARQYN\n"
        "Выбери действие:"
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
        
        buttons = []
        for university in universities:
            title = university.get("name", "")
            buttons.append([InlineKeyboardButton(title, callback_data=f"show_university_events_{university.get('id')}")])
        buttons.append([InlineKeyboardButton("Назад", callback_data="back_to_menu")])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await query.edit_message_text(text="Выберите о чем вы хотите узнать:", reply_markup=markup)
        
        
        
    elif data.startswith('show_university_events_'):
        try:
            university_id = int(data.split('_')[-1])
        except ValueError:
            await query.edit_message_text(text="Неверный идентификатор практики.")
            return
        universities = db.get_universities()
        university = next(
            (u for u in universities if u.get("id") == university_id),
            None
        )
        if university:
            response = ""
            instagram_link = university['instagram']
            if instagram_link.startswith('@'):
                instagram_link = instagram_link[1:]
                instagram_link = f"https://instagram.com/{instagram_link}"
            else:
                instagram_link = f"https://instagram.com/{instagram_link}"
            response += f"<strong>{university['name']}</strong>\r\n"
            response += f"{university['description']}\r\n"
            
            if university["link"]["url"] and university["link"]["title"]: # if we have both url and title
                response += f"<a href='{university['link']['url']}'>{university['link']['title']}</a>\n\n"
            elif university["link"]["title"] and not university["link"]["url"]: # if we have title
                response += f"<a href='{instagram_link}'>{university["link"]['title']}</a>\n\n"
            elif university["link"]["url"] and not university["link"]["title"]: # if we have url
                response += f"<a href='{university['link']['url']}'>Ссылка на сайт</a>\n\n"
            response += f"<a href='{instagram_link}'>Ссылка на Instagram</a>\n\n"
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Назад", callback_data="university_info")]
            ])
            
            # add events to message 
            events = db.get_university_events(university_id)
            if events:
                response += "События:\n"
                for event in events:
                    response += f"<strong>{event.get('title')}</strong>\n"
                    response += f"Дата проведения: {event.get('date')}\n"
                    response += f"Описание: {event.get('description')}\n"
                    response += f"<a href='{event.get('link')}'>Узнать подробнее об инвенте</a>\n\n"
            await query.edit_message_text(text=response, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text="Университет не найден.")
        
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
            response += f"Цена: {format_price(psychologist.get("price"))} \r\n"
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
            "Привет, я - DOS\n"
            "Друг проекта JARQYN\n"
            "Выбери действие:"
        )
        await query.edit_message_text(text=text, reply_markup=start_menu)

    elif data == 'practices':
        categories = db.get_practice_categories()
        if not categories:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
            ])
            await query.edit_message_text(text="Нет доступных практик.", reply_markup=markup)
            return

        buttons = []
        for category in categories:
            title = category
            buttons.append([InlineKeyboardButton(title, callback_data=f"show_category_{categories.index(category)}")])
        buttons.append([InlineKeyboardButton("Назад", callback_data="back_to_menu")])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await query.edit_message_text(text="Выберите категорию практик:", reply_markup=markup)

    elif data.startswith("show_category_"):
        category_index = int(data.split('_')[-1])
        categories = db.get_practice_categories()
        practices_data = db.get_practices_by_category(categories[category_index])
        if not practices_data:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
            ])
            await query.edit_message_text(text="Нет доступных практик.", reply_markup=markup)
            return

        buttons = []
        row = []
        response = ""
        for index, practice in enumerate(practices_data, start=1):
            title = practice.get("name", "")
            description = practice.get('description', '')
            response += f"{index}. <strong>{title}</strong>\n"
            response += f"{(description  + '\n') if description else ''}"

            # Create button
            button = InlineKeyboardButton(str(index), callback_data=f"show_practice_{practice.get('id')}")
            row.append(button)

            # Add row every 2 buttons
            if len(row) == 2:
                buttons.append(row)
                row = []

        # Append the last row if it has only one button
        if row:
            buttons.append(row)

        # Add the "Назад" button as a separate row
        buttons.append([InlineKeyboardButton("Назад", callback_data="practices")])

        markup = InlineKeyboardMarkup(buttons)

        response += "\nВыберите практику:"
        await query.edit_message_text(text=response, reply_markup=markup, parse_mode=ParseMode.HTML)
            
    elif data.startswith('show_practice_'):
        try:
            practice_id = int(data.split('_')[-1])
        except ValueError:
            await query.edit_message_text(text="Неверный идентификатор практики.")
            return
        practices_data = db.get_practices()
        categories = db.get_practice_categories()
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
                [InlineKeyboardButton("Назад", callback_data=f"show_category_{categories.index(practice.get('category'))}")]
            ])
            await query.edit_message_text(text=content, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text="Практика не найдена.")

    else:
        await query.edit_message_text(text="Неизвестная команда.")

async def receive_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle user issue reports
    admin_ids = db.get_admin_ids()
    if not admin_ids:
        await update.message.reply_text("Произошла ошибка при отправке сообщения.")
        return
    for admin_id in admin_ids:
        message = f"Ошибка от пользователя {update.effective_chat.id}:\n{update.message.text}"
        await context.bot.send_message(admin_id, message)
        
    await update.message.reply_text("Спасибо! Мы рассмотрим вашу проблему.")

# Global variable to store last known practice IDs
last_practice_ids = set()

async def check_new_practices_job(context: ContextTypes.DEFAULT_TYPE):
    global last_practice_ids
    try:
        practices = db.get_practices()
        current_ids = {practice.get("id") for practice in practices if practice.get("id") is not None}
        logging.info(f"Fetched {len(current_ids)} practices.")
        if not last_practice_ids:
            last_practice_ids = current_ids
            logging.info("Initialized practice IDs without announcement.")
            return
        new_ids = current_ids - last_practice_ids
        if new_ids:
            new_practices = [practice for practice in practices if practice.get("id") in new_ids]
            logging.info(f"Detected {len(new_practices)} new practices: {new_ids}")
            message = "Новые практики:\n\n"
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
            for user in user_ids:
                try:
                    await context.bot.send_message(chat_id=user, text=message, reply_markup=markup, parse_mode=ParseMode.HTML)
                    logging.info(f"Sent new practice announcement to user {user}.")
                except Exception as e:
                    logging.error(f"Error sending announcement to user {user}: {str(e)}")
        else:
            logging.info("No new practices found.")
        last_practice_ids = current_ids
    except Exception as e:
        logging.error(f"Error in check_new_practices_job: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_issue))
    # Schedule periodic job for new practices check every 1 minute (60 seconds)
    application.job_queue.run_repeating(check_new_practices_job, interval=60, first=0)
    logging.info("Bot started and job scheduled.")
    # Start the bot (this will run until interrupted)
    application.run_polling(poll_interval=2)
    

if __name__ == '__main__':
    main()
