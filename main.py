from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
import db, nest_asyncio, asyncio
from categories import university, psychologist, practices, contacts

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
        [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
    ]),
    "psychologist_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить психолога", callback_data='add_psychologist')],
        [InlineKeyboardButton("Удалить психолога", callback_data='delete_psychologist')],
        [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
    ]),
    "practices_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Ангст", callback_data='practice_anxiety')],
        [InlineKeyboardButton("Стресс", callback_data='practice_stress')],
        [InlineKeyboardButton("Добавить практику", callback_data='add_practices')],
        [InlineKeyboardButton("Удалить практику", callback_data='delete_practices')],
        [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
    ]),
    "contacts_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить контакт", callback_data='add_contacts')],
        [InlineKeyboardButton("Удалить контакт", callback_data='delete_contacts')],
        [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
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
        "Привет, меня зовут Dos!\n"
        "Я друг проекта психологической поддержки Jarqyn.\n"
        "Я помогу справиться с тревогой, стрессом, выгоранием.\n"
        "Выберите действие:", reply_markup=reply_markup)

def get_info(category):
    return db.get_bot_info(category)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Delegate category handling
    if query.data == 'admin_category_university':
        return await university.admin_menu(update, context, replies)
    elif query.data == 'admin_category_psychologist':
        return await psychologist.admin_menu(update, context, replies)
    elif query.data == 'admin_category_practices':
        return await practices.admin_menu(update, context, replies)
    elif query.data == 'admin_category_contacts':
        return await contacts.admin_menu(update, context, replies)
    
    if query.data in ['practice_anxiety', 'practice_stress']:
        # New handling for sample practices
        sample_text = {
            "practice_anxiety": "Практика для тревожности:\n\n1. Сядьте удобно.\n2. Закройте глаза.\n3. Сфокусируйтесь на дыхании.\n4. Представьте, как уходит тревога.",
            "practice_stress": "Практика для стресса:\n\n1. Найдите тихое место.\n2. Сделайте глубокий вдох.\n3. Медленно выдохните.\n4. Сконцентрируйтесь на настоящем моменте."
        }
        await query.message.edit_text(sample_text[query.data])
        return

    if query.data in ['find_psychologist', 'practices', 'university_info', 'contacts']:
        response = get_info(query.data)
        back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_menu")]])
        await query.message.edit_text(response, reply_markup=back_markup)
        return
    elif query.data == 'report_issue':
        response = "Опишите вашу проблему, и мы постараемся её решить. Отправьте сообщение в чат."
        back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_menu")]])
        await query.message.edit_text(response, reply_markup=back_markup)
        return

    elif query.data == 'admin_panel':
        admin_keyboard = [
            [InlineKeyboardButton("Университеты", callback_data='admin_category_university')],
            [InlineKeyboardButton("Психологи", callback_data='admin_category_psychologist')],
            [InlineKeyboardButton("Практики", callback_data='admin_category_practices')],
            [InlineKeyboardButton("Контакты", callback_data='admin_category_contacts')],
            [InlineKeyboardButton("Назад в меню", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(admin_keyboard)
        await query.message.edit_text("Выберите админ действие:", reply_markup=reply_markup)
        return

    elif query.data == 'add_university':
        context.user_data['pending_admin_action'] = 'add_university'
        await query.message.edit_text("Введите название университета:")
        return

    elif query.data == 'add_psychologist':
        context.user_data['pending_admin_action'] = 'add_psychologist'
        await query.message.edit_text("Введите данные для нового психолога. Желательно в формате: Имя Фамилия, Специализация, Номер Телефона, инстаграм (если имеется)")
        return

    elif query.data == 'add_practices':
        context.user_data['pending_admin_action'] = 'add_practices'
        await query.message.edit_text("Введите данные для новой практики")
        return

    elif query.data == 'add_contacts':
        context.user_data['pending_admin_action'] = 'add_contacts'
        await query.message.edit_text("Введите новые данные для контакта")
        return

    elif query.data == 'delete_university':
        # Fetch university info from JSON DB
        data = db.fetch_db()
        rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'university']
        if not rows:
            await query.message.edit_text("Нет университетов для удаления.")
            return
        uni_buttons = []
        delete_map = {}
        for idx, entry in enumerate(rows):
            key = str(idx)
            delete_map[key] = entry["info"]
            uni_name = entry["info"].split(";")[0]
            uni_buttons.append([InlineKeyboardButton(uni_name, callback_data=f'delete_university_{key}')])
        context.user_data['delete_universities'] = delete_map
        uni_buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_university')])
        reply_markup = InlineKeyboardMarkup(uni_buttons)
        await query.message.edit_text("Выберите университет для удаления:", reply_markup=reply_markup)
        return

    elif query.data == 'delete_psychologist':
        data = db.fetch_db()
        rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'psychologist']
        if not rows:
            await query.message.edit_text("Нет психологов для удаления.")
            return
        buttons = []
        delete_map = {}
        for idx, entry in enumerate(rows):
            key = str(idx)
            delete_map[key] = entry["info"]
            buttons.append([InlineKeyboardButton(entry["info"], callback_data=f'delete_psychologist_{key}')])
        context.user_data['delete_psychologist'] = delete_map
        buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_psychologist')])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text("Выберите психолога для удаления:", reply_markup=reply_markup)
        return

    elif query.data == 'delete_practices':
        data = db.fetch_db()
        rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'practices']
        if not rows:
            await query.message.edit_text("Нет практик для удаления.")
            return
        buttons = []
        delete_map = {}
        for idx, entry in enumerate(rows):
            key = str(idx)
            delete_map[key] = entry["info"]
            buttons.append([InlineKeyboardButton(entry["info"], callback_data=f'delete_practices_{key}')])
        context.user_data['delete_practices'] = delete_map
        buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_practices')])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text("Выберите практику для удаления:", reply_markup=reply_markup)
        return

    elif query.data == 'delete_contacts':
        data = db.fetch_db()
        rows = [entry for entry in data.get("bot_info", []) if entry["category"] == 'contacts']
        if not rows:
            await query.message.edit_text("Нет контактов для удаления.")
            return
        buttons = []
        delete_map = {}
        for idx, entry in enumerate(rows):
            key = str(idx)
            delete_map[key] = entry["info"]
            buttons.append([InlineKeyboardButton(entry["info"], callback_data=f'delete_contacts_{key}')])
        context.user_data['delete_contacts'] = delete_map
        buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_contacts')])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text("Выберите контакт для удаления:", reply_markup=reply_markup)
        return

    elif query.data.startswith('delete_university_'):
        key = query.data.split('_')[-1]
        uni_info = context.user_data.get('delete_universities', {}).get(key)
        if not uni_info:
            await query.message.edit_text("Ошибка: данные не найдены.")
            return
        context.user_data['pending_delete_uni'] = key
        confirm_keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data=f'confirm_delete_university_{key}')],
            [InlineKeyboardButton("Отмена", callback_data='cancel_delete_university')]
        ]
        reply_markup = InlineKeyboardMarkup(confirm_keyboard)
        uni_name = uni_info.split(";")[0]
        await query.message.edit_text(f"Подтвердите удаление: {uni_name}", reply_markup=reply_markup)
        return

    elif query.data.startswith('delete_psychologist_'):
        key = query.data.split('_')[-1]
        info = context.user_data.get('delete_psychologist', {}).get(key)
        if not info:
            await query.message.edit_text("Ошибка: данные не найдены.")
            return
        context.user_data['pending_delete_psychologist'] = key
        confirm_keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data=f'confirm_delete_psychologist_{key}')],
            [InlineKeyboardButton("Отмена", callback_data='cancel_delete_psychologist')]
        ]
        reply_markup = InlineKeyboardMarkup(confirm_keyboard)
        await query.message.edit_text(f"Подтвердите удаление: {info}", reply_markup=reply_markup)
        return

    elif query.data.startswith('delete_practices_'):
        key = query.data.split('_')[-1]
        info = context.user_data.get('delete_practices', {}).get(key)
        if not info:
            await query.message.edit_text("Ошибка: данные не найдены.")
            return
        context.user_data['pending_delete_practices'] = key
        confirm_keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data=f'confirm_delete_practices_{key}')],
            [InlineKeyboardButton("Отмена", callback_data='cancel_delete_practices')]
        ]
        reply_markup = InlineKeyboardMarkup(confirm_keyboard)
        await query.message.edit_text(f"Подтвердите удаление: {info}", reply_markup=reply_markup)
        return

    elif query.data.startswith('delete_contacts_'):
        key = query.data.split('_')[-1]
        info = context.user_data.get('delete_contacts', {}).get(key)
        if not info:
            await query.message.edit_text("Ошибка: данные не найдены.")
            return
        context.user_data['pending_delete_contacts'] = key
        confirm_keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data=f'confirm_delete_contacts_{key}')],
            [InlineKeyboardButton("Отмена", callback_data='cancel_delete_contacts')]
        ]
        reply_markup = InlineKeyboardMarkup(confirm_keyboard)
        await query.message.edit_text(f"Подтвердите удаление: {info}", reply_markup=reply_markup)
        return

    elif query.data.startswith('confirm_delete_university_'):
        key = query.data.split('_')[-1]
        uni_info = context.user_data.get('delete_universities', {}).get(key)
        if uni_info and db.delete_bot_info('university', uni_info):
            await query.message.edit_text("Университет удалён.")
        else:
            await query.message.edit_text("Ошибка при удалении.")
        context.user_data.pop('pending_delete_uni', None)
        context.user_data.pop('delete_universities', None)
        admin_keyboard = [
            [InlineKeyboardButton("Добавить университет", callback_data='add_university')],
            [InlineKeyboardButton("Удалить университет", callback_data='delete_university')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(admin_keyboard)
        await query.message.reply_text("Выберите другое действие или вернитесь:", reply_markup=reply_markup)
        return

    elif query.data.startswith('confirm_delete_psychologist_'):
        key = query.data.split('_')[-1]
        info = context.user_data.get('delete_psychologist', {}).get(key)
        if info and db.delete_bot_info('psychologist', info):
            await query.message.edit_text("Психолог удалён.")
        else:
            await query.message.edit_text("Ошибка при удалении.")
        context.user_data.pop('pending_delete_psychologist', None)
        context.user_data.pop('delete_psychologist', None)
        psy_keyboard = [
            [InlineKeyboardButton("Добавить психолога", callback_data='add_psychologist')],
            [InlineKeyboardButton("Удалить психолога", callback_data='delete_psychologist')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(psy_keyboard)
        await query.message.reply_text("Выберите другое действие или вернитесь:", reply_markup=reply_markup)
        return

    elif query.data.startswith('confirm_delete_practices_'):
        key = query.data.split('_')[-1]
        info = context.user_data.get('delete_practices', {}).get(key)
        if info and db.delete_bot_info('practices', info):
            await query.message.edit_text("Практика удалена.")
        else:
            await query.message.edit_text("Ошибка при удалении.")
        context.user_data.pop('pending_delete_practices', None)
        context.user_data.pop('delete_practices', None)
        prac_keyboard = [
            [InlineKeyboardButton("Добавить практику", callback_data='add_practices')],
            [InlineKeyboardButton("Удалить практику", callback_data='delete_practices')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(prac_keyboard)
        await query.message.reply_text("Выберите другое действие или вернитесь:", reply_markup=reply_markup)
        return

    elif query.data.startswith('confirm_delete_contacts_'):
        key = query.data.split('_')[-1]
        info = context.user_data.get('delete_contacts', {}).get(key)
        if info and db.delete_bot_info('contacts', info):
            await query.message.edit_text("Контакт удалён.")
        else:
            await query.message.edit_text("Ошибка при удалении.")
        context.user_data.pop('pending_delete_contacts', None)
        context.user_data.pop('delete_contacts', None)
        cont_keyboard = [
            [InlineKeyboardButton("Добавить контакт", callback_data='add_contacts')],
            [InlineKeyboardButton("Удалить контакт", callback_data='delete_contacts')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(cont_keyboard)
        await query.message.reply_text("Выберите другое действие или вернитесь:", reply_markup=reply_markup)
        return

    elif query.data == 'cancel_delete_university':
        await query.message.edit_text("Удаление отменено.")
        admin_keyboard = [
            [InlineKeyboardButton("Добавить университет", callback_data='add_university')],
            [InlineKeyboardButton("Удалить университет", callback_data='delete_university')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(admin_keyboard)
        await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        return

    elif query.data == 'cancel_delete_psychologist':
        await query.message.edit_text("Удаление отменено.")
        psy_keyboard = [
            [InlineKeyboardButton("Добавить психолога", callback_data='add_psychologist')],
            [InlineKeyboardButton("Удалить психолога", callback_data='delete_psychologist')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(psy_keyboard)
        await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        return

    elif query.data == 'cancel_delete_practices':
        await query.message.edit_text("Удаление отменено.")
        prac_keyboard = [
            [InlineKeyboardButton("Добавить практику", callback_data='add_practices')],
            [InlineKeyboardButton("Удалить практику", callback_data='delete_practices')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(prac_keyboard)
        await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        return

    elif query.data == 'cancel_delete_contacts':
        await query.message.edit_text("Удаление отменено.")
        cont_keyboard = [
            [InlineKeyboardButton("Добавить контакт", callback_data='add_contacts')],
            [InlineKeyboardButton("Удалить контакт", callback_data='delete_contacts')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(cont_keyboard)
        await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        return

    elif query.data == 'back_to_menu':
        await query.message.edit_text(
            "Привет, меня зовут Dos!\n"
            "Я друг проекта психологической поддержки Jarqyn.\n"
            "Я помогу справиться с тревогой, стрессом, выгоранием.\n"
            "Выберите действие:", reply_markup=replies["start_menu"])
        return

    elif query.data in ['admin_announce']:
        instructions = {"admin_announce": "Чтобы отправить объявление, используйте команду /announce ..."}
        response = instructions.get(query.data, "")
    
    else:
        response = "Неизвестная команда."
    await query.message.edit_text(response)

async def receive_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id in get_admin_ids() and context.user_data.get('pending_admin_action'):
        action = context.user_data['pending_admin_action']
        text = update.message.text
        if action == 'announcement':
            users = db.get_users()
            for chat_id in users:
                await context.bot.send_message(chat_id=chat_id, text=text)
            await update.message.reply_text("Объявление успешно отправлено.")
            return
        elif action == 'add_university':
            await university.process_university_input(update, context)
            return
        elif action == 'add_psychologist':
            await psychologist.process_psychologist_input(update, context)
            return
        # Rest of admin actions
        elif action == 'add_practices':
            db.add_bot_info('practices', text)
            await update.message.reply_text("Практика добавлена.")
        elif action == 'add_contacts':
            db.add_bot_info('contacts', text)
            await update.message.reply_text("Контакт добавлен.")
        context.user_data.pop('pending_admin_action', None)
        return
    user_message = update.message.text
    await update.message.reply_text("Спасибо! Мы рассмотрим вашу проблему.")

async def send_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in [str(x) for x in get_admin_ids()]:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return
    users = db.get_users()
    message = " ".join(context.args)
    media = update.message.photo or update.message.video
    for chat_id in users:
        if media:
            if update.message.photo:
                await context.bot.send_photo(chat_id=chat_id, photo=update.message.photo[-1].file_id, caption=message)
            elif update.message.video:
                await context.bot.send_video(chat_id=chat_id, video=update.message.video.file_id, caption=message)
        else:
            await context.bot.send_message(chat_id=chat_id, text=message)
    await update.message.reply_text("Объявление успешно отправлено всем пользователям.")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_issue))
    app.add_handler(CommandHandler("announce", send_announcement))
    await app.run_polling()

nest_asyncio.apply()

if __name__ == "__main__":
    asyncio.run(main())
