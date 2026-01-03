"""
vidinie centralized logging utility

provides consistent logging configuration across all modules.
all modules should import and use this logger instead of creating their own.
"""

import logging
import logging.handlers
import sys
from typing import Optional
import os


# ansi color codes
class Colors:
    """ansi color codes for terminal output"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GREY = '\033[90m'


class ColoredFormatter(logging.Formatter):
    """custom formatter that adds colors to entire log messages"""
    
    # color mapping for different log levels
    COLORS = {
        logging.DEBUG: Colors.YELLOW,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED,
    }
    
    def format(self, record):
        """format the log record with colors applied to entire message including log content"""
        # get the color for this log level
        color = self.COLORS.get(record.levelno, Colors.RESET)
        
        # format the message normally first
        formatted = super().format(record)
        
        # wrap the entire formatted message (timestamp, name, level, and message) in color
        return f"{color}{formatted}{Colors.RESET}"


# global configuration
_configured = False
_log_dir: Optional[str] = None


def setup_logging(
    level: int = logging.INFO,
    log_dir: Optional[str] = None,
    format_string: Optional[str] = None,
    use_colors: bool = True,
) -> None:
    """
    set up the global logging configuration.
    this should be called once at application startup.
    args:
        level: logging level (e.g., logging.INFO, logging.DEBUG)
        log_dir: optional path to log directory. if provided, logs to both console and file
        format_string: custom format string. if none, uses default format
        use_colors: whether to use colored output in console (default: True)
    """
    global _configured, _log_dir
    
    if _configured:
        return  # already configured
    # default format string
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # remove existing handlers
    root_logger.handlers.clear()
    # console handler with optional colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    if use_colors:
        console_formatter = ColoredFormatter(format_string)
    else:
        console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    # file handler (if specified)
    if log_dir:
        _log_dir = log_dir
        # create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        # create rotating file handler (rotates daily at midnight)
        # old log files are automatically renamed with date suffix: filename.YYYY-MM-DD
        # example: vidinie.log -> vidinie.log.2024-01-15
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(log_dir, 'vidinie.log'),
            when='midnight',        # rotate at midnight
            interval=1,             # every 1 day
            backupCount=30,  # keep this many old log files
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    get a logger for a specific module.
    args:
        name: name of the module (typically __name__)
    returns:
        configured logger instance
    example:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Starting processing...")
    """
    # ensure logging is configured
    if not _configured:
        setup_logging()
    # get logger for the specified module
    return logging.getLogger(name)


def set_level(level: int) -> None:
    """
    change the logging level dynamically.
    args:
        level: new logging level (e.g., logging.DEBUG, logging.INFO)
    returns:
        none
    example:
        from utils.logger import set_level, get_logger
        logger = get_logger(__name__)
        set_level(logging.DEBUG)
        logger.debug("This is a debug message")
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # set level for all handlers
    for handler in root_logger.handlers:
        handler.setLevel(level)


def get_log_dir() -> Optional[str]:
    """
    get the current log directory.
    returns:
        path to log directory or None if not logging to file
    example:
        from utils.logger import get_log_dir
        log_dir = get_log_dir()
        print(f"Log directory: {log_dir}")
    """
    return _log_dir

