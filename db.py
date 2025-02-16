import requests, os
from dotenv import load_dotenv
from typing import Dict, List, Any
from utils import logger

load_dotenv()

API_URL = str(os.getenv("NPOINT_URL"))

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

def handle_api_errors(func):
    """Decorator to handle API errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.RequestException as e:
            logger.error(f"API error in {func.__name__}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    return wrapper

@handle_api_errors
def fetch_db() -> Dict[str, Any]:
    """Fetch database content"""
    response = requests.get(API_URL)
    response.raise_for_status()
    return response.json()

@handle_api_errors
def update_db(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update database content"""
    response = requests.post(API_URL, json=data)
    response.raise_for_status()
    return response.json()

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2 format.
    
    Args:
        text (str): Text to escape
        
    Returns:
        str: Escaped text safe for MarkdownV2
        
    Examples:
        >>> escape_markdown("Hello! Cost: $5.99")
        'Hello\\! Cost: \\$5\\.99'
        >>> escape_markdown("*bold* _italic_")
        '\\*bold\\* \\_italic\\_'
    """
    if not isinstance(text, str):
        return str(text)  # Convert non-strings to strings
        
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', 
                    '-', '=', '|', '{', '}', '.', '!', '$']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def get_bot_info() -> str:
    return {
        "practices": get_practices(),
        "find_psychologist": get_psychologists(),
        "university_info": get_universities(),
        "contacts": get_contacts()
    }
            
def get_practices() -> str:
    """Get formatted practices info"""
    try:
        data = fetch_db()
        practices = data.get("bot_info", [])
        if not practices:
            return escape_markdown("Нет практик.")
        return format_list_entries(practices, "practices")
    except Exception as e:
        logger.error(f"Error fetching practices: {str(e)}")
        return escape_markdown("Временно недоступно. Попробуйте позже.")
 
def get_psychologists() -> str:
    """Get formatted psychologists info"""
    try:
        data = fetch_db()
        psychologists = data.get("bot_info", [])
        if not psychologists:
            return escape_markdown("Нет психологов.")
        return format_list_entries(psychologists, "psychologists")
    except Exception as e:
        logger.error(f"Error fetching psychologists: {str(e)}")
        return escape_markdown("Временно недоступно. Попробуйте позже.")

def get_universities() -> str:
    """Get formatted universities info"""
    try:
        data = fetch_db()
        universities = data.get("bot_info", [])
        if not universities:
            return escape_markdown("Нет университетов.")
        return format_list_entries(universities, "university_info")
    except Exception as e:
        logger.error(f"Error fetching universities: {str(e)}")
        return escape_markdown("Временно недоступно. Попробуйте позже.")

def get_contacts() -> str:
    """Get formatted contacts info"""
    try:
        data = fetch_db()
        contacts = data.get("bot_info", [])
        if not contacts:
            return escape_markdown("Нет контактов.")
        return format_list_entries(contacts, "contacts")
    except Exception as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        return escape_markdown("Временно недоступно. Попробуйте позже.")

def format_list_entries(entries: list, category: str) -> str:
    """Format list entries with proper numbering and line breaks"""
    formatted_entries = []
    
    for idx, entry in enumerate(entries, 1):
        formatted = ""  # Initialize formatted string
        
        if isinstance(entry, dict):
            if category == 'psychologists':
                # Format structured psychologist data
                name = entry.get('name', '')
                specialty = entry.get('specialty', '')
                instagram = entry.get('instagram')
                contacts = entry.get('contacts')
                price = entry.get('price')
                
                formatted = f"{idx}\\. *{escape_markdown(name)}*"
                if specialty:
                    formatted += f"\r\nСпециализация: {escape_markdown(specialty)}"
                if instagram:
                    formatted += f"\r\nInstagram: {escape_markdown(instagram)}"
                if contacts:
                    phone = contacts.get('phone', '')
                    if phone:
                        formatted += f"\r\nТелефон: {escape_markdown(phone)}"
                if price:
                    formatted += f"\r\nСтоимость: {escape_markdown(str(price))} тг\\."
                else:
                    formatted += f"\r\nСтоимость: Цена не указана"
                    
            elif category == 'practices':
                # Format structured practice data
                name = entry.get('name', '')
                content = entry.get('content', '')
                author = entry.get('author')
                
                formatted = f"{idx}\\. *{escape_markdown(name)}*"
                if content:
                    formatted += f"\r\n{escape_markdown(content)}"
                if author:
                    formatted += f"\r\n\r\n_Автор: {escape_markdown(author)}_"
                    
            elif category == 'university_info':
                # Format structured university data
                name = entry.get('name', '')
                instagram = entry.get('instagram', '')
                
                formatted = f"{idx}\\. {escape_markdown(name)}"
                if instagram:
                    formatted += f"\r\nInstagram: {escape_markdown(instagram)}"
                    
            elif category == 'contacts':
                # Format structured contact data
                phone = entry.get('phone', '')
                formatted = f"{idx}\\. {escape_markdown(phone)}"
                
        else:  # Handle legacy string format
            formatted = f"{idx}\\. {escape_markdown(str(entry))}"
            
        formatted_entries.append(formatted)
    
    return "\n\n".join(formatted_entries)

def add_bot_info(category: str, info: dict) -> Dict[str, Any]:
    """
    Add new bot info entry with validation.
    
    Args:
        category (str): Category for the new entry
        info (dict): Information to store
        
    Returns:
        Dict[str, Any]: New entry data
        
    Raises:
        DatabaseError: If database operation fails
        ValueError: If input validation fails
    """
    if not category or not info:
        raise ValueError("Category and info must not be empty")
        
    try:
        data = fetch_db()
        bot_info = data.get("bot_info", [])
        
        # Generate new ID safely
        new_id = max([entry.get("id", 0) for entry in bot_info], default=0) + 1
        
        new_entry = {
            "id": new_id,
            "category": category,
            "info": info
        }
        
        bot_info.append(new_entry)
        data["bot_info"] = bot_info
        update_db(data)
        
        logger.info(f"Added new {category} entry with ID {new_id}")
        return new_entry
        
    except Exception as e:
        logger.error(f"Error adding bot info: {str(e)}")
        raise DatabaseError(f"Failed to add bot info: {str(e)}")
    
def add_psychologist(name: str, specialty: str, instagram: str, contacts: dict, price: int) -> Dict[str, Any]:
    return add_bot_info("psychologists", {
        "name": name,
        "specialty": specialty,
        "instagram": instagram,
        "contacts": contacts,
        "price": price
    })

def add_practice(name: str, content: str, author: str) -> Dict[str, Any]:
    return add_bot_info("practices", {
        "name": name,
        "content": content,
        "author": author
    })
    
def add_university(name: str, instagram: str) -> Dict[str, Any]:
    return add_bot_info("university_info", {
        "name": name,
        "instagram": instagram
    })
    
def add_contact(phone: str) -> Dict[str, Any]:
    return add_bot_info("contacts", {
        "phone": phone
    })


def delete_bot_info(category: str, info: str) -> bool:
    """Delete bot info entry"""
    try:
        data = fetch_db()
        bot_info = data.get("bot_info", [])
        initial_length = len(bot_info)
        bot_info = [entry for entry in bot_info if not (entry["category"] == category and entry["info"] == info)]
        data["bot_info"] = bot_info
        update_db(data)
        return len(bot_info) != initial_length
    except Exception as e:
        logger.error(f"Error deleting bot info: {str(e)}")
        raise DatabaseError(f"Failed to delete bot info: {str(e)}")
    
def delete_by_id(category: str, id: int) -> bool:
    """Delete bot info entry by ID"""
    try:
        data = fetch_db()
        bot_info = data.get("bot_info", [])
        initial_length = len(bot_info)
        bot_info = [entry for entry in bot_info if not (entry["category"] == category and entry["id"] == id)]
        data["bot_info"] = bot_info
        update_db(data)
        return len(bot_info) != initial_length
    except Exception as e:
        logger.error(f"Error deleting bot info: {str(e)}")
        raise DatabaseError(f"Failed to delete bot info: {str(e)}")

def get_users() -> List[int]:
    """Get list of user chat IDs"""
    try:
        data = fetch_db()
        return data.get("users", [])
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return []

def add_user(chat_id: int) -> List[int]:
    """Add new user chat ID"""
    try:
        data = fetch_db()
        users = data.get("users", [])
        if chat_id not in users:
            users.append(chat_id)
            data["users"] = users
            update_db(data)
        return users
    except Exception as e:
        logger.error(f"Error adding user: {str(e)}")
        raise DatabaseError(f"Failed to add user: {str(e)}")

def get_admin_ids() -> List[int]:
    """Get list of admin chat IDs from database"""
    try:
        data = fetch_db()
        return [int(x) for x in data.get("admin_ids", [])]
    except Exception as e:
        logger.error(f"Error fetching admin IDs: {str(e)}")
        return []

