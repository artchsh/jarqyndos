import requests, os, logging, time
from typing import Optional, List
from classes import Data, Contact, Event, Psychologist, Practice, University
import json

logger = logging.getLogger(__name__)

# from env.json import NPOINT_URL
with open("env.json", "r") as f:
    env = json.load(f)

API_URL = env["NPOINT_URL"]

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

_cache_ttl = 60  # cache duration in seconds
_db_cache: Optional[Data] = None
_db_cache_timestamp: float = 0.0

def fetch_db() -> Data:
    """Fetch database content with caching"""
    global _db_cache, _db_cache_timestamp
    current_time = time.time()
    if _db_cache is not None and (current_time - _db_cache_timestamp) < _cache_ttl:
        return _db_cache
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        _db_cache = data
        _db_cache_timestamp = current_time
        return data
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
    
def get_start_text() -> str:
    """Get formatted start text"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    start_text = bot_info.get("start_text", "")
    # If no start text is found in the database, use a default message
    if not start_text:
        start_text = "Привет, я - DOS 🤖\nДруг проекта JARQYN\n"
    
    text = start_text + "\nВыбери действие из меню ниже:"
    return text
            
def get_practices() -> List[Practice]:
    """Get formatted practices info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    practices = bot_info.get("practices", [])
    return practices

def get_practice_categories() -> List[str]:
    practices = get_practices()
    categories = []
    for practice in practices:
        if not practice["category"] in categories:
            categories.append(practice["category"])
    return categories

def get_practices_by_category(category_name: str) -> List[Practice]:
    practices = get_practices()
    filtered_practices = []
    for practice in practices:
        if practice["category"] == category_name:
            filtered_practices.append(practice)
            
    return filtered_practices
 
def get_psychologists() -> List[Psychologist]:
    """Get formatted psychologists info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    psychologists = bot_info.get("psychologists", [])
    return psychologists 

def get_universities() -> List[University]:
    """Get formatted universities info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    universities = bot_info.get("universities", [])
    return universities

def get_contacts() -> List[Contact]:
    """Get formatted contacts info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    contacts = bot_info.get("contacts", [])
    return contacts

def get_events() -> List[Event]:
    """Get formatted events info"""
    data = fetch_db()
    bot_info = data.get("bot_info", [])
    events = bot_info.get("events", [])
    return events

def get_university_events(university_id: str) -> List[Event]:
    """Get events for a specific university"""
    events = get_events()
    events = [event for event in events if event.get("universityId") == university_id]
    return events

def get_admin_ids() -> List[int]:
    """Get admin chat IDs"""
    data = fetch_db()
    return data.get("admin_ids", [])

def add_user(chat_id: int) -> List[int]:
    """Add new user chat ID"""
    data = fetch_db()
    users = data.get("users", [])
    if chat_id not in users:
        users.append(chat_id)
        data["users"] = users
        update_db(data)
    return users

def get_users() -> List[int]:
    """Get list of user chat IDs"""
    data = fetch_db()
    return data.get("users", [])