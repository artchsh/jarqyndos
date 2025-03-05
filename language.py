import json
from types import SimpleNamespace
from logger import logger

def load_language_file():
    """Load language strings from JSON file and convert to nested namespaces for dot notation access"""
    try:
        with open("language.json", "r", encoding="utf-8") as file:
            language_data = json.load(file)
        
        # Convert the JSON to a nested SimpleNamespace for dot notation access
        def dict_to_namespace(d):
            if isinstance(d, dict):
                for key, value in d.items():
                    if isinstance(value, dict):
                        d[key] = dict_to_namespace(value)
                return SimpleNamespace(**d)
            return d
        
        textjson = dict_to_namespace(language_data)
        logger.info("Language strings loaded successfully")
        return textjson
    except Exception as e:
        logger.error(f"Failed to load language strings: {str(e)}")
        # Return a basic namespace in case of error
        return SimpleNamespace()

# Create textjson instance to be imported by other modules
textjson = load_language_file()
