from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_IDS = [int(x.strip()) for x in os.getenv("ADMIN_CHAT_IDS", "").split(",") if x]
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_DATABASE")
)
cursor = db.cursor()

def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Найти психолога", callback_data='find_psychologist')],
        [InlineKeyboardButton("Практики", callback_data='practices')],
        [InlineKeyboardButton("Jarqyn в твоем университете", callback_data='university_info')],
        [InlineKeyboardButton("Контакты", callback_data='contacts')],
        [InlineKeyboardButton("Сообщить об ошибке", callback_data='report_issue')]
    ]
    if update.message.chat_id in ADMIN_CHAT_IDS:
        keyboard.append([InlineKeyboardButton("Админ панель", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Привет, меня зовут Dos!\n"
        "Я друг проекта психологической поддержки Jarqyn.\n"
        "Я помогу справиться с тревогой, стрессом, выгоранием.\n"
        "Выберите действие:", reply_markup=reply_markup)

def get_info(category):
    cursor.execute(f"SELECT info FROM bot_info WHERE category = %s", (category,))
    result = cursor.fetchall()
    return "\n".join([row[0] for row in result]) if result else "Нет данных."

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'find_psychologist':
        response = get_info('find_psychologist')
    elif query.data == 'practices':
        response = get_info('practices')
    elif query.data == 'university_info':
        response = get_info('university_info')
    elif query.data == 'contacts':
        response = get_info('contacts')
    elif query.data == 'report_issue':
        response = "Опишите вашу проблему, и мы постараемся её решить. Отправьте сообщение в чат."
    
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

    elif query.data == 'admin_category_university':
        uni_keyboard = [
            [InlineKeyboardButton("Добавить университет", callback_data='add_university')],
            [InlineKeyboardButton("Удалить университет", callback_data='delete_university')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(uni_keyboard)
        await query.message.edit_text("Университеты — выберите действие:", reply_markup=reply_markup)
        return

    elif query.data == 'admin_category_psychologist':
        psy_keyboard = [
            [InlineKeyboardButton("Добавить психолога", callback_data='add_psychologist')],
            [InlineKeyboardButton("Удалить психолога", callback_data='delete_psychologist')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(psy_keyboard)
        await query.message.edit_text("Психологи — выберите действие:", reply_markup=reply_markup)
        return

    elif query.data == 'admin_category_practices':
        prac_keyboard = [
            [InlineKeyboardButton("Добавить практику", callback_data='add_practices')],
            [InlineKeyboardButton("Удалить практику", callback_data='delete_practices')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(prac_keyboard)
        await query.message.edit_text("Практики — выберите действие:", reply_markup=reply_markup)
        return

    elif query.data == 'admin_category_contacts':
        cont_keyboard = [
            [InlineKeyboardButton("Добавить контакт", callback_data='add_contacts')],
            [InlineKeyboardButton("Удалить контакт", callback_data='delete_contacts')],
            [InlineKeyboardButton("Назад", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(cont_keyboard)
        await query.message.edit_text("Контакты — выберите действие:", reply_markup=reply_markup)
        return

    elif query.data == 'back_to_admin':
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
        await query.message.edit_text("Введите данные для нового университета в формате: название;ссылка")
        return

    elif query.data == 'add_psychologist':
        context.user_data['pending_admin_action'] = 'add_psychologist'
        await query.message.edit_text("Введите данные для нового психолога")
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
        cursor.execute("SELECT info FROM bot_info WHERE category = %s", ('university',))
        rows = cursor.fetchall()
        if not rows:
            await query.message.edit_text("Нет университетов для удаления.")
            return
        uni_buttons = []
        delete_map = {}
        for idx, row in enumerate(rows):
            key = str(idx)
            delete_map[key] = row[0]
            uni_name = row[0].split(";")[0]
            uni_buttons.append([InlineKeyboardButton(uni_name, callback_data=f'delete_university_{key}')])
        context.user_data['delete_universities'] = delete_map
        uni_buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_university')])
        reply_markup = InlineKeyboardMarkup(uni_buttons)
        await query.message.edit_text("Выберите университет для удаления:", reply_markup=reply_markup)
        return

    elif query.data == 'delete_psychologist':
        cursor.execute("SELECT info FROM bot_info WHERE category = %s", ('psychologist',))
        rows = cursor.fetchall()
        if not rows:
            await query.message.edit_text("Нет психологов для удаления.")
            return
        buttons = []
        delete_map = {}
        for idx, row in enumerate(rows):
            key = str(idx)
            delete_map[key] = row[0]
            buttons.append([InlineKeyboardButton(row[0], callback_data=f'delete_psychologist_{key}')])
        context.user_data['delete_psychologist'] = delete_map
        buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_psychologist')])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text("Выберите психолога для удаления:", reply_markup=reply_markup)
        return

    elif query.data == 'delete_practices':
        cursor.execute("SELECT info FROM bot_info WHERE category = %s", ('practices',))
        rows = cursor.fetchall()
        if not rows:
            await query.message.edit_text("Нет практик для удаления.")
            return
        buttons = []
        delete_map = {}
        for idx, row in enumerate(rows):
            key = str(idx)
            delete_map[key] = row[0]
            buttons.append([InlineKeyboardButton(row[0], callback_data=f'delete_practices_{key}')])
        context.user_data['delete_practices'] = delete_map
        buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_practices')])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text("Выберите практику для удаления:", reply_markup=reply_markup)
        return

    elif query.data == 'delete_contacts':
        cursor.execute("SELECT info FROM bot_info WHERE category = %s", ('contacts',))
        rows = cursor.fetchall()
        if not rows:
            await query.message.edit_text("Нет контактов для удаления.")
            return
        buttons = []
        delete_map = {}
        for idx, row in enumerate(rows):
            key = str(idx)
            delete_map[key] = row[0]
            buttons.append([InlineKeyboardButton(row[0], callback_data=f'delete_contacts_{key}')])
        context.user_data['delete_contacts'] = delete_map
        buttons.append([InlineKeyboardButton("Назад", callback_data='admin_category_contacts')])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text("Выберите контакт для удаления:", reply_markup=reply_markup)
        return

    elif query.data.startswith('delete_uni_'):
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
        if uni_info:
            cursor.execute("DELETE FROM bot_info WHERE category = %s AND info = %s", ('university', uni_info))
            db.commit()
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
        if info:
            cursor.execute("DELETE FROM bot_info WHERE category = %s AND info = %s", ('psychologist', info))
            db.commit()
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
        if info:
            cursor.execute("DELETE FROM bot_info WHERE category = %s AND info = %s", ('practices', info))
            db.commit()
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
        if info:
            cursor.execute("DELETE FROM bot_info WHERE category = %s AND info = %s", ('contacts', info))
            db.commit()
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
        keyboard = [
            [InlineKeyboardButton("Найти психолога", callback_data='find_psychologist')],
            [InlineKeyboardButton("Практики", callback_data='practices')],
            [InlineKeyboardButton("Jarqyn в твоем университете", callback_data='university_info')],
            [InlineKeyboardButton("Контакты", callback_data='contacts')],
            [InlineKeyboardButton("Сообщить об ошибке", callback_data='report_issue')]
        ]
        if query.message.chat_id in ADMIN_CHAT_IDS:
            keyboard.append([InlineKeyboardButton("Админ панель", callback_data='admin_panel')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("Выберите действие:", reply_markup=reply_markup)
        return

    elif query.data in ['admin_announce']:
        instructions = {"admin_announce": "Чтобы отправить объявление, используйте команду /announce ..."}
        response = instructions.get(query.data, "")
    
    else:
        response = "Неизвестная команда."
    
    await query.message.edit_text(response)

async def receive_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id in ADMIN_CHAT_IDS and context.user_data.get('pending_admin_action'):
        action = context.user_data['pending_admin_action']
        text = update.message.text
        if action == 'add_university':
            if ";" not in text:
                await update.message.reply_text("Неверный формат. Ожидается: название;ссылка")
                return
            name, link = [s.strip() for s in text.split(";", 1)]
            info = f"{name};{link}"
            cursor.execute("INSERT INTO bot_info (category, info) VALUES (%s, %s)", ('university', info))
            db.commit()
            await update.message.reply_text(f"Университет '{name}' добавлен.")
        elif action == 'add_psychologist':
            cursor.execute("INSERT INTO bot_info (category, info) VALUES (%s, %s)", ('psychologist', text))
            db.commit()
            await update.message.reply_text("Психолог добавлен.")
        elif action == 'add_practices':
            cursor.execute("INSERT INTO bot_info (category, info) VALUES (%s, %s)", ('practices', text))
            db.commit()
            await update.message.reply_text("Практика добавлена.")
        elif action == 'add_contacts':
            cursor.execute("INSERT INTO bot_info (category, info) VALUES (%s, %s)", ('contacts', text))
            db.commit()
            await update.message.reply_text("Контакт добавлен.")
        context.user_data.pop('pending_admin_action', None)
        return

    user_message = update.message.text
    await update.message.reply_text("Спасибо! Мы рассмотрим вашу проблему.")

async def send_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in [str(x) for x in ADMIN_CHAT_IDS]:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return
    
    users_cursor = db.cursor()
    users_cursor.execute("SELECT chat_id FROM users")
    users = users_cursor.fetchall()
    message = " ".join(context.args)
    media = update.message.photo or update.message.video
    
    for user in users:
        chat_id = user[0]
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

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
