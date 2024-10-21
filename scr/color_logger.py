# color_logger.py
import logging
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    def format(self, record):
        log_msg = super().format(record)
        if record.levelno == logging.WARNING:
            return f"{Fore.YELLOW}{log_msg}{Fore.RESET}"
        return log_msg

# Set up the logger as a singleton
logger = logging.getLogger("my_logger")

if not logger.hasHandlers():  # Check if the logger already has handlers
    logger.setLevel(logging.DEBUG)  # Set level to DEBUG or desired level
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Show DEBUG and above
    
    # Set formatter
    formatter = ColorFormatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)