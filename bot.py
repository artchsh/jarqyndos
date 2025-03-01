import db, logging, sys, json
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode

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

# Define more specific conversation states for better navigation
(MAIN_MENU, UNIVERSITY_MENU, FIND_PSYCHOLOGIST, PRACTICES_MENU, 
 PRACTICE_CATEGORY, PRACTICE_DETAIL, CONTACTS_MENU, REPORT_ISSUE) = range(8)

# Replace inline keyboard with reply keyboard for main menu
start_menu = ReplyKeyboardMarkup([
    ["Узнать о JARQYN 🧑‍🤝‍🧑"],
    ["Найти психолога 🧠"],
    ["Практики 🧘‍♀️"],
    ["Контакты 📞"],
    ["Сообщить об ошибке ⚠️"]
], resize_keyboard=True)

# Back button for reply keyboard
back_button = ReplyKeyboardMarkup([["Назад ↩️"]], resize_keyboard=True)

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
    # Store an empty navigation stack in user_data
    context.user_data['nav_stack'] = []
    
    text = (
        "Привет, я - DOS 🤖\n"
        "Друг проекта JARQYN\n"
        "Выбери действие из меню ниже:"
    )
    await update.message.reply_text(text, reply_markup=start_menu)
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from the main menu"""
    text = update.message.text.split(" ")[0]  # Remove emoji if present
    
    # Reset navigation stack when at main menu
    context.user_data['nav_stack'] = []
    
    if text == "Узнать":
        # Push current state to stack before moving to new state
        context.user_data['nav_stack'].append(MAIN_MENU)
        return await handle_university_info(update, context)
    elif text == "Найти":
        context.user_data['nav_stack'].append(MAIN_MENU)
        return await handle_find_psychologist(update, context)
    elif text == "Практики":
        context.user_data['nav_stack'].append(MAIN_MENU)
        return await handle_practices(update, context)
    elif text == "Контакты":
        context.user_data['nav_stack'].append(MAIN_MENU)
        return await handle_contacts(update, context)
    elif text == "Сообщить":
        context.user_data['nav_stack'].append(MAIN_MENU)
        await update.message.reply_text(
            "Пожалуйста, опиши ошибку или проблему, с которой ты столкнулся. Я постараюсь исправить её как можно скорее! 🛠️",
            reply_markup=back_button
        )
        return REPORT_ISSUE
    else:
        await update.message.reply_text("Пожалуйста, выбери один из вариантов в меню 👇", reply_markup=start_menu)
        return MAIN_MENU

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle going back to the previous state"""
    nav_stack = context.user_data.get('nav_stack', [])
    
    if not nav_stack:
        # If stack is empty, go to main menu
        text = (
            "Привет, я - DOS 🤖\n"
            "Друг проекта JARQYN\n"
            "Выбери действие из меню ниже:"
        )
        await update.message.reply_text(text, reply_markup=start_menu)
        return MAIN_MENU
    
    # Pop the last state from stack
    prev_state = nav_stack.pop()
    
    # Navigate to previous state
    if prev_state == MAIN_MENU:
        text = (
            "Возвращаемся в главное меню 🏠\n"
            "Выбери действие из меню ниже:"
        )
        await update.message.reply_text(text, reply_markup=start_menu)
        return MAIN_MENU
    elif prev_state == UNIVERSITY_MENU:
        return await handle_university_info(update, context)
    elif prev_state == PRACTICES_MENU:
        return await handle_practices(update, context)
    elif prev_state == PRACTICE_CATEGORY:
        # Get the category from user_data and return to that category
        category = context.user_data.get('current_category')
        if category:
            return await show_practice_category(update, context, category)
        else:
            return await handle_practices(update, context)
    else:
        # Default to main menu if state is unknown
        text = (
            "Извини, что-то пошло не так 😕\n"
            "Возвращаемся в главное меню"
        )
        await update.message.reply_text(text, reply_markup=start_menu)
        return MAIN_MENU

async def handle_university_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    universities = db.get_universities()
    if not universities:
        await update.message.reply_text("К сожалению, информация о университетах пока недоступна 😔", reply_markup=back_button)
        return UNIVERSITY_MENU
    
    keyboard = []
    for university in universities:
        keyboard.append([university.get("name", "") + " 🎓"])
    keyboard.append(["Назад ↩️"])
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text("Выбери университет, о котором хочешь узнать больше: 👇", reply_markup=markup)
    
    # Store universities in context for later use
    context.user_data['universities'] = universities
    return UNIVERSITY_MENU

async def university_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Назад ↩️" or text == "Назад":
        return await go_back(update, context)
    
    # Remove emoji if present
    text = text.split(" 🎓")[0] if " 🎓" in text else text
    
    universities = context.user_data.get('universities', [])
    university = next((u for u in universities if u.get("name") == text), None)
    
    if not university:
        await update.message.reply_text("Извини, университет не найден 🔍", reply_markup=back_button)
        return UNIVERSITY_MENU
    
    university_id = university.get("id")
    response = ""
    instagram_link = university['instagram']
    if instagram_link.startswith('@'):
        instagram_link = instagram_link[1:]
        instagram_link = f"https://instagram.com/{instagram_link}"
    else:
        instagram_link = f"https://instagram.com/{instagram_link}"
    
    response += f"<strong>{university['name']} 🎓</strong>\r\n\r\n"
    response += f"{university['description']}\r\n\r\n"
    
    if university["link"]["url"] and university["link"]["title"]:
        response += f"<a href='{university['link']['url']}'>{university['link']['title']}</a>\n\n"
    elif university["link"]["title"] and not university["link"]["url"]:
        response += f"<a href='{instagram_link}'>{university['link']['title']}</a>\n\n"
    elif university["link"]["url"] and not university["link"]["title"]:
        response += f"<a href='{university['link']['url']}'>Посетить сайт 🌐</a>\n\n"
    
    response += f"<a href='{instagram_link}'>Instagram 📱</a>\n\n"
    
    events = db.get_university_events(university_id)
    if events:
        response += "📅 <strong>Предстоящие события:</strong>\n\n"
        for event in events:
            response += f"<strong>{event.get('title')}</strong>\n"
            response += f"📆 Дата: {event.get('date')}\n"
            response += f"ℹ️ {event.get('description')}\n"
            response += f"<a href='{event.get('link')}'>Подробнее о событии 👈</a>\n\n"
    
    await update.message.reply_text(response, reply_markup=back_button, parse_mode=ParseMode.HTML)
    return UNIVERSITY_MENU

async def handle_find_psychologist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psychologists = db.get_psychologists()
    if not psychologists:
        await update.message.reply_text("К сожалению, информация о психологах пока недоступна 😔", reply_markup=back_button)
        return FIND_PSYCHOLOGIST
    
    response = ""
    for psychologist in psychologists:
        instagram_link = psychologist.get("instagram", "")
        if instagram_link.startswith('@'):
            instagram_link = instagram_link[1:]
        instagram_link = f"https://instagram.com/{instagram_link}"
        
        if psychologist.get("price", 0) == 0:
            psychologist["price"] = "Уточнить"
        response += f"<strong>{psychologist.get('name', '')} 👨‍⚕️</strong>\r\n"
        response += f"🧠 Специализация: {psychologist.get('specialty', '')}\r\n"
        response += f"💰 Цена: {format_price(psychologist.get('price'))} \r\n"
        response += f"📞 Телефон: <a href='tel:{psychologist['contacts']['phone']}'>{psychologist['contacts']['phone']}</a>\r\n"
        response += f"<a href='{instagram_link}'>Instagram 📱</a>\n\n"
    
    await update.message.reply_text(response, reply_markup=back_button, parse_mode=ParseMode.HTML)
    return FIND_PSYCHOLOGIST

async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contacts = db.get_contacts()
    if not contacts:
        await update.message.reply_text("К сожалению, контактная информация пока недоступна 😔", reply_markup=back_button)
        return CONTACTS_MENU
    
    response = "📞 <strong>Наши контакты:</strong>\n\n"
    for contact in contacts:
        response += f"<strong>{contact.get('name', '')}</strong>\r\n"
        response += f"📞 Телефон: <a href='tel:{contact.get('phone', '')}'>{contact.get('phone', '')}</a>\r\n"
        response += f"📧 Email: <a href='mailto:{contact.get('email', '')}'>{contact.get('email', '')}</a>\n\n"
    
    await update.message.reply_text(response, reply_markup=back_button, parse_mode=ParseMode.HTML)
    return CONTACTS_MENU

async def handle_practices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = db.get_practice_categories()
    if not categories:
        await update.message.reply_text("К сожалению, практики пока недоступны 😔", reply_markup=back_button)
        return PRACTICES_MENU
    
    keyboard = []
    for category in categories:
        keyboard.append([category + " 🧘‍♀️"])
    keyboard.append(["Назад ↩️"])
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Store categories for later use
    context.user_data['practice_categories'] = categories
    
    await update.message.reply_text("Выбери категорию практик, которая вас интересует: 👇", reply_markup=markup)
    return PRACTICES_MENU

async def practices_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Назад ↩️" or text == "Назад":
        return await go_back(update, context)
    
    # Remove emoji if present
    text = text.split(" 🧘‍♀️")[0] if " 🧘‍♀️" in text else text
    
    categories = context.user_data.get('practice_categories', [])
    if text not in categories:
        await update.message.reply_text("Извини, такая категория не найдена 🔍", reply_markup=back_button)
        return PRACTICES_MENU
    
    # Store the previous state and category
    context.user_data['nav_stack'].append(PRACTICES_MENU)
    return await show_practice_category(update, context, text)

async def show_practice_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category=None):
    if not category:
        category = context.user_data.get('current_category')
        if not category:
            await update.message.reply_text("Извини, что-то пошло не так 😕", reply_markup=start_menu)
            return MAIN_MENU
    
    practices_data = db.get_practices_by_category(category)
    if not practices_data:
        await update.message.reply_text(f"В категории '{category}' пока нет доступных практик 😔", reply_markup=back_button)
        return PRACTICE_CATEGORY
    
    buttons = []
    row = []
    response = f"<strong>Категория: {category} 🧘‍♀️</strong>\n\n"
    for index, practice in enumerate(practices_data, start=1):
        title = practice.get("name", "")
        description = practice.get('description', '')
        response += f"{index}. <strong>{title}</strong>\n"
        response += f"{(description  + '\n') if description else ''}"
        
        button = InlineKeyboardButton(str(index), callback_data=f"show_practice_{practice.get('id')}")
        row.append(button)
        
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    inline_markup = InlineKeyboardMarkup(buttons)
    context.user_data['current_category'] = category
    
    response += "\n👆 Выбери практику, нажав на соответствующий номер:"
    await update.message.reply_text(response, reply_markup=inline_markup, parse_mode=ParseMode.HTML)
    return PRACTICE_CATEGORY

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith('show_practice_'):
        try:
            practice_id = int(data.split('_')[-1])
        except ValueError:
            await query.edit_message_text(text="Неверный идентификатор практики 😕")
            return PRACTICE_CATEGORY
        
        practices_data = db.get_practices()
        practice = next(
            (p for p in practices_data if p.get("id") == practice_id),
            None
        )
        
        if practice:
            name = practice.get("name", "")
            name = f"<strong>{name} 🧘‍♀️</strong>\n\n"
            content = name + practice.get("content", "")
            if practice.get("author"):
                content += f"\n\n👤 Автор: {practice.get('author')}"
            
            # Push current state to navigation stack
            context.user_data['nav_stack'].append(PRACTICE_CATEGORY)
            context.user_data['current_practice_id'] = practice_id
            
            await query.edit_message_text(text=content, parse_mode=ParseMode.HTML)
            
            # Send a new message with back button
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Для возврата к списку практик нажми 'Назад ↩️'",
                reply_markup=back_button
            )
            return PRACTICE_DETAIL
        else:
            await query.edit_message_text(text="К сожалению, данная практика не найдена 😕")
            return PRACTICE_CATEGORY

async def practice_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Назад ↩️" or text == "Назад":
        return await go_back(update, context)
    
    await update.message.reply_text("Для возврата к списку практик нажми 'Назад ↩️'", reply_markup=back_button)
    return PRACTICE_DETAIL

async def report_issue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Назад ↩️" or text == "Назад":
        return await go_back(update, context)
    
    # Handle user issue reports
    admin_ids = db.get_admin_ids()
    if not admin_ids:
        await update.message.reply_text("Извини, произошла ошибка при отправке сообщения 😕", reply_markup=back_button)
        return REPORT_ISSUE
    
    for admin_id in admin_ids:
        message = f"⚠️ Сообщение об ошибке от пользователя {update.effective_chat.id}:\n\n{update.message.text}"
        await context.bot.send_message(admin_id, message)
    
    await update.message.reply_text("Спасибо! Я получил ваше сообщение и скоро займусь решением проблемы 👍", reply_markup=start_menu)
    return MAIN_MENU

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Извини, что-то пошло не так 😕 Давай начнем сначала.",
        reply_markup=start_menu
    )
    return MAIN_MENU

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
    
    # Create conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            UNIVERSITY_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, university_menu_handler)],
            FIND_PSYCHOLOGIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, go_back)],
            CONTACTS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, go_back)],
            PRACTICES_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, practices_menu_handler)],
            PRACTICE_CATEGORY: [
                CallbackQueryHandler(button_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, go_back)
            ],
            PRACTICE_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, practice_detail_handler)],
            REPORT_ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_issue_handler)],
        },
        fallbacks=[CommandHandler("start", start), MessageHandler(filters.ALL, fallback_handler)],
    )
    
    application.add_handler(conv_handler)
    
    # Schedule periodic job for new practices check every 1 minute (60 seconds)
    application.job_queue.run_repeating(check_new_practices_job, interval=60, first=0)
    logging.info("Bot started and job scheduled.")
    
    # Start the bot (this will run until interrupted)
    application.run_polling(poll_interval=2)

if __name__ == '__main__':
    main()
