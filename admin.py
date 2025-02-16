from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, 
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
)
from categories import university, psychologist, practices, contacts
import db
from utils import logger

# Category handlers mapping
CATEGORY_HANDLERS = {
    'university': {
        'module': university,
        'conv_handler': university.university_conv_handler,
        'menu_key': 'university_menu'
    },
    'psychologist': {
        'module': psychologist,
        'conv_handler': psychologist.psychologist_conv_handler,
        'menu_key': 'psychologist_menu'
    },
    'practices': {
        'module': practices,
        'conv_handler': practices.practice_conv_handler,
        'menu_key': 'practices_menu'
    },
    'contacts': {
        'module': contacts,
        'conv_handler': contacts.contacts_conv_handler,
        'menu_key': 'contacts_menu'
    }
}

# Admin menu keyboard
admin_replies = {
    "admin_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("Университеты", callback_data='admin_category_university')],
        [InlineKeyboardButton("Психологи", callback_data='admin_category_psychologist')],
        [InlineKeyboardButton("Практики", callback_data='admin_category_practices')],
        [InlineKeyboardButton("Контакты", callback_data='admin_category_contacts')],
        [InlineKeyboardButton("Отправить объявление", callback_data='send_announcement')],
        [InlineKeyboardButton("Назад в меню", callback_data='back_to_menu')]
    ]),
    # Category-specific menus
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
    ]),
    # Back buttons
    "back_to_admin_menu": InlineKeyboardMarkup([[
        InlineKeyboardButton("Назад", callback_data='admin_panel')
    ]]),
    "back_to_menu": InlineKeyboardMarkup([[
        InlineKeyboardButton("Назад в меню", callback_data='back_to_menu')
    ]])
}

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin-related callback queries"""
    query = update.callback_query
    
    # Handle category menu navigation
    if query.data.startswith('admin_category_'):
        category = query.data.replace('admin_category_', '')
        if category in CATEGORY_HANDLERS:
            return await CATEGORY_HANDLERS[category]['module'].admin_menu(
                update, context, admin_replies
            )
    
    # Handle add actions
    elif query.data.startswith('add_'):
        category = query.data.replace('add_', '')
        if category in CATEGORY_HANDLERS:
            return await CATEGORY_HANDLERS[category]['module'].start_add(update, context)
    
    # Handle delete actions
    elif query.data.startswith('delete_'):
        category = query.data.replace('delete_', '')
        if category in CATEGORY_HANDLERS:
            return await CATEGORY_HANDLERS[category]['module'].delete_handler(update, context)
            
    # Handle admin panel display
    elif query.data == 'admin_panel':
        return await show_admin_panel(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel menu"""
    await update.callback_query.message.edit_text(
        "Выберите админ действие:", 
        reply_markup=admin_replies["admin_menu"]
    )

async def send_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send announcement to all users"""
    if str(update.message.chat_id) not in [str(x) for x in db.get_admin_ids()]:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return
        
    users = db.get_users()
    message = " ".join(context.args)
    media = update.message.photo or update.message.video
    
    for chat_id in users:
        try:
            if media:
                if update.message.photo:
                    await context.bot.send_photo(
                        chat_id=chat_id, 
                        photo=update.message.photo[-1].file_id, 
                        caption=message
                    )
                elif update.message.video:
                    await context.bot.send_video(
                        chat_id=chat_id, 
                        video=update.message.video.file_id, 
                        caption=message
                    )
            else:
                await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send announcement to {chat_id}: {str(e)}")
            continue
            
    await update.message.reply_text("Объявление успешно отправлено всем пользователям.")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle text messages from admins with pending actions"""
    action = context.user_data.get('pending_admin_action')
    if not action:
        return False
        
    # Map actions to their handlers
    action_handlers = {
        'announcement': handle_announcement,
        'add_university': university.process_university_input,
        'add_psychologist': psychologist.process_psychologist_input,
        'add_practices': practices.process_practice_input,
        'add_contacts': contacts.process_contact_input
    }
    
    if action in action_handlers:
        await action_handlers[action](update, context)
        return True
    
    return False

async def handle_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle announcement message"""
    users = db.get_users()
    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=update.message.text)
        except Exception as e:
            logger.error(f"Failed to send announcement to {chat_id}: {str(e)}")
            continue
    await update.message.reply_text("Объявление успешно отправлено.")

def register_admin_handlers(application: Application) -> None:
    """Register all admin-related handlers"""
    
    # Register conversation handlers first
    for handler_info in CATEGORY_HANDLERS.values():
        if 'conv_handler' in handler_info:
            application.add_handler(handler_info['conv_handler'])
    
    # Register command handlers
    application.add_handler(CommandHandler("announce", send_announcement))
    
    # Register callback query handlers for admin menu navigation
    # This should be after conversation handlers but before general callback handler
    application.add_handler(
        CallbackQueryHandler(
            handle_admin_callback,
            pattern="^(admin_|delete_)"  # Remove add_ as it's handled by conversation handlers
        )
    ) 