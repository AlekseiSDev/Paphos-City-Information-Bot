# utils.py

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    Sets up the logger to log user interactions into logs/bot.log.
    Creates the logs directory if it doesn't exist.
    
    :return: Configured logger instance.
    """
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    logger = logging.getLogger('paphos_bot_logger')
    logger.setLevel(logging.INFO)
    
    # Define log format
    formatter = logging.Formatter('%(asctime)s - userid %(user_id)s - %(action)s')
    
    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'bot.log'),
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Avoid adding multiple handlers if logger already has handlers
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger

def log_user_action(logger, user_id, action_description):
    """
    Logs the user's action in a structured format.
    
    :param logger: Logger instance.
    :param user_id: Telegram user ID.
    :param action_description: Description of the action performed by the user.
    """
    logger.info('', extra={'user_id': user_id, 'action': action_description})
