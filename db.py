import requests, os
import logging
from dotenv import load_dotenv
from typing import Dict, List, Any
from typing import TypedDict, Optional

logger = logging.getLogger(__name__)

class Practice(TypedDict):
    id: str
    name: str
    content: str
    author: Optional[str]

class Contacts(TypedDict):
    name: Optional[str]
    phone: str
    email: str
    
class Psychologist(TypedDict):
    name: str
    specialty: str
    instagram: str
    contacts: Contacts
    price: int

class University(TypedDict):
    name: str
    instagram: str
    
class BotInfo(TypedDict):
    practices: List[Practice]
    psychologists: List[Psychologist]
    universities: List[University]
    contacts: List[Contacts]

class Users(List[int]):
    pass

class Data(TypedDict):
    bot_info: BotInfo
    users: Users
    admin_ids: Users


load_dotenv()

API_URL = str(os.getenv("NPOINT_URL"))

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

def fetch_db() -> Data:
    """Fetch database content"""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching database: {str(e)}")
        raise DatabaseError(f"Failed to fetch database: {str(e)}")

def update_db(data: Data) -> Data:
    """Update database content"""
    try:
        response = requests.post(API_URL, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        raise DatabaseError(f"Failed to update database: {str(e)}")

def get_bot_info() -> BotInfo:
    return {
        "practices": get_practices(),
        "find_psychologist": get_psychologists(),
        "university_info": get_universities(),
        "contacts": get_contacts()
    }
            
def get_practices():
    """Get formatted practices info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    practices: List[Practice] | list = bot_info.get("practices", [])
    return practices

 
def get_psychologists():
    """Get formatted psychologists info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    psychologists: List[Psychologist] | list = bot_info.get("psychologists", [])
    return psychologists 

def get_universities():
    """Get formatted universities info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    universities: List[University] | list= bot_info.get("universities", [])
    return universities

def get_contacts():
    """Get formatted contacts info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    contacts: List[Contacts] | List[None] = bot_info.get("contacts", [])
    return contacts

def add_user(chat_id: int) -> List[int]:
    """Add new user chat ID"""
    data = fetch_db()
    users = data.get("users", [])
    if chat_id not in users:
        users.append(chat_id)
        data["users"] = users
        update_db(data)
    return users