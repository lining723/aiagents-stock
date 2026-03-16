import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(name=None, log_file=None, level=logging.INFO):
    """
    配置统一的日志系统
    
    Args:
        name: 日志器名称，默认使用 __name__
        log_file: 日志文件路径，默认 log/app.log
        level: 日志级别，默认 INFO
    
    Returns:
        logging.Logger: 配置好的日志器
    """
    if name is None:
        name = __name__
    
    if log_file is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, 'log')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'app.log')
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    logger.propagate = False
    
    log_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name=None):
    """
    获取日志器，如果未配置则自动配置
    
    Args:
        name: 日志器名称
    
    Returns:
        logging.Logger: 配置好的日志器
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


_root_logger = setup_logger('aiagents_stock')
