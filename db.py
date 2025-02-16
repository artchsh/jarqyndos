import requests, os
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
from utils import logger, ValidationError

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

def get_bot_info(category: str) -> str:
    """Get formatted info for a category"""
    try:
        data = fetch_db()
        bot_info = data.get("bot_info", [])
        entries = [entry["info"] for entry in bot_info if entry["category"] == category]
        logger.info(f"Fetched {category} info: {entries}")
        if not entries:
            return "Нет данных."
        if category in ['university_info', 'find_psychologist']:
            formatted_entries = []
            for entry in entries:
                if category == "find_psychologist":
                    parts = entry.split("\n")
                    if parts:
                        # Capitalize and bold the name (first line) then add remaining lines indented
                        name = parts[0].strip().upper()
                        formatted = f"• *{name}*"
                        if len(parts) > 1:
                            rest = "\n  ".join(parts[1:])
                            formatted += f"\n  {rest}"
                        formatted_entries.append(formatted)
                    else:
                        formatted_entries.append(entry)
                else:
                    formatted_entries.append(f"• {entry}")
            return "\n".join(formatted_entries)
        else:
            return "\n".join(entries)
    except Exception as e:
        logger.error(f"Error fetching {category} info: {str(e)}")
        return "Временно недоступно. Попробуйте позже."

def add_bot_info(category: str, info: str) -> Dict[str, Any]:
    """Add new bot info entry"""
    try:
        data = fetch_db()
        bot_info = data.get("bot_info", [])
        new_id = max([entry["id"] for entry in bot_info], default=0) + 1
        new_entry = {"id": new_id, "category": category, "info": info}
        bot_info.append(new_entry)
        data["bot_info"] = bot_info
        update_db(data)
        return new_entry
    except Exception as e:
        logger.error(f"Error adding bot info: {str(e)}")
        raise DatabaseError(f"Failed to add bot info: {str(e)}")

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

def add_admin(chat_id: int) -> List[int]:
    """Add new admin chat ID"""
    try:
        data = fetch_db()
        admin_ids = data.get("admin_ids", [])
        if str(chat_id) not in admin_ids:
            admin_ids.append(str(chat_id))
            data["admin_ids"] = admin_ids
            update_db(data)
        return admin_ids
    except Exception as e:
        logger.error(f"Error adding admin: {str(e)}")
        raise DatabaseError(f"Failed to add admin: {str(e)}")
