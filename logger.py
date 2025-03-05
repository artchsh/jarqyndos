import logging
import sys

def setup_logger():
    """Configure and return the application logger"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("JarqynBot")
    return logger

# Create logger instance to be imported by other modules
logger = setup_logger()
