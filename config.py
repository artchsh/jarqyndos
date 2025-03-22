import json
from logger import logger

# Load environment variables from env.json
try:
    with open("env.json", "r") as f:
        env = json.load(f)
    
    TOKEN = env["TOKEN"]
    logger.info("Environment configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load environment configuration: {str(e)}")
    raise

# Define conversation states
(MAIN_MENU, UNIVERSITY_MENU, FIND_PSYCHOLOGIST, PRACTICES_MENU, 
 PRACTICE_CATEGORY, PRACTICE_DETAIL, CONTACTS_MENU, REPORT_ISSUE, PARTNERS_MENU) = range(9)

# Global variable to store last known practice IDs
last_practice_ids = set()
