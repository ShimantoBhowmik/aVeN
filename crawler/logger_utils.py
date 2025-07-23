"""
Logging utilities for the web crawler
"""

import logging
import os
from datetime import datetime
from constants import DEFAULT_LOGS_FOLDER


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with both file and console handlers
    
    Args:
        name: Logger name
        log_file: Log file name (optional)
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(DEFAULT_LOGS_FOLDER, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"crawler_{timestamp}.log"
    
    file_path = os.path.join(DEFAULT_LOGS_FOLDER, log_file)
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (only for INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_crawler_logger() -> logging.Logger:
    """Get the main crawler logger"""
    return setup_logger('crawler', 'crawler.log')


def get_content_logger() -> logging.Logger:
    """Get the content processing logger"""
    return setup_logger('content', 'content.log')


def get_file_logger() -> logging.Logger:
    """Get the file operations logger"""
    return setup_logger('file_ops', 'file_operations.log')
