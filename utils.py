import logging
from typing import Dict
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

def validate_text(text: str, min_length: int = 1, max_length: int = 1000) -> bool:
    """Validate text length and content"""
    return min_length <= len(text) <= max_length and not all(c.isspace() for c in text)

def validate_url(url: str) -> bool:
    """Basic URL validation"""
    return url.startswith(('http://', 'https://', '@'))

def validate_price(price: str) -> bool:
    """Validate price format"""
    try:
        value = int(price)
        return value >= 0
    except ValueError:
        return False

class DataValidator:
    @staticmethod
    def psychologist(data: Dict[str, str]) -> bool:
        # expect keys: name, specialty, instagram, price
        required = ["name", "specialty", "instagram", "price"]
        for key in required:
            if key not in data or not validate_text(data[key], min_length=2):
                return False
        return True

    @staticmethod
    def university(data: Dict[str, str]) -> bool:
        # expect keys: name, instagram
        required = ["name", "instagram"]
        for key in required:
            if key not in data or not validate_text(data[key], min_length=2):
                return False
        return True
    
    @staticmethod
    def practice(data: Dict[str, str]) -> bool:
        # expect keys: name, content, author
        required = ["name", "content"]
        for key in required:
            if key not in data or not validate_text(data[key], min_length=2):
                return False
        return True

    @staticmethod
    def contact(data: Dict[str, str]) -> bool:
        # expect keys: phone
        required = ["phone"]
        for key in required:
            if key not in data or not validate_text(data[key], min_length=2):
                return False
        return True

def error_handler(func):
    """Decorator for error handling and logging"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise e
    return wrapper

def validate_admin_action(func):
    """Decorator to validate admin actions"""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        from db import get_admin_ids  # local import to avoid circular dependency
        if update.effective_user.id not in get_admin_ids():
            await update.callback_query.message.edit_text("Недостаточно прав для выполнения этого действия.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
