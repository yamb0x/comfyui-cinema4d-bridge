"""
Logging configuration and utilities
"""

import sys
from pathlib import Path
from loguru import logger
from datetime import datetime


def setup_logging(log_dir: Path = None, debug: bool = True):
    """
    Setup application logging with loguru
    
    Args:
        log_dir: Directory to store log files
        debug: Enable debug logging
    """
    # Remove default logger
    logger.remove()
    
    # Console logging with color
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # File logging
    if log_dir is None:
        log_dir = Path("D:/Yambo Studio Dropbox/Admin/_studio-dashboard-app-dev/comfy-to-c4d/logs")
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Detailed log file
    log_file = log_dir / f"comfy_to_c4d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="100 MB",
        retention="7 days",
        compression="zip"
    )
    
    # Error log file
    error_log = log_dir / "errors.log"
    logger.add(
        error_log,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="50 MB",
        retention="30 days",
        backtrace=True,
        diagnose=True
    )
    
    logger.info(f"Logging initialized. Log directory: {log_dir}")
    logger.info(f"Main log file: {log_file}")
    
    return logger


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self):
        """Get logger instance for this class"""
        return logger.bind(classname=self.__class__.__name__)