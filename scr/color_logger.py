import logging
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    def format(self, record):
        """
        Formats log messages with color based on the logging level.

        Overrides the default format method of the logging.Formatter class
        to apply colors to warning messages.

        Args:
            record (logging.LogRecord): The log record containing the information
                to be formatted.

        Returns:
            str: The formatted log message with appropriate colors based on the 
            log level.

        Notes:
            - Warning messages will be colored yellow.
            - Other log levels will be formatted normally without colors.
        """
        log_msg = super().format(record)
        if record.levelno == logging.WARNING:
            return f"{Fore.YELLOW}{log_msg}{Fore.RESET}"
        return log_msg

logger = logging.getLogger("my_logger")

if not logger.hasHandlers():  # Check if the logger already has handlers
    """
    Initializes the logger configuration if no handlers are set.

    Sets the logging level to DEBUG, creates a console handler that displays
    log messages in the console, and applies the ColorFormatter to format
    the log messages.

    This configuration ensures that all log messages of level DEBUG and above
    are displayed, with warning messages highlighted in yellow.

    Notes:
        - The console handler is only added if the logger has no existing handlers,
        preventing duplicate messages.
    """
    logger.setLevel(logging.DEBUG)  # Set level to DEBUG or desired level
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Show DEBUG and above

    formatter = ColorFormatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)