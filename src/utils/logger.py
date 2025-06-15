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
    
    # Console logging with color and UTF-8 encoding
    level = "DEBUG" if debug else "INFO"
    
    # For Windows, we need to handle encoding properly
    import platform
    if platform.system() == "Windows":
        # Force UTF-8 encoding for Windows console
        import os
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
    # Configure console output based on platform
    if platform.system() == "Windows":
        # For Windows, use a custom sink that handles encoding
        import codecs
        
        class SafeConsoleSink:
            def __init__(self):
                self.stream = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
                
            def write(self, message):
                try:
                    # Remove color codes if encoding fails
                    clean_message = message
                    if hasattr(self.stream, 'isatty') and not self.stream.isatty():
                        import re
                        clean_message = re.sub(r'\x1b\[[0-9;]*m', '', message)
                    self.stream.write(clean_message)
                    self.stream.flush()
                except Exception:
                    # Fallback: print without colors or special chars
                    import re
                    clean_message = re.sub(r'\x1b\[[0-9;]*m', '', message)
                    clean_message = clean_message.encode('ascii', 'replace').decode('ascii')
                    print(clean_message, end='', flush=True)
        
        logger.add(
            SafeConsoleSink(),
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True
        )
    else:
        # For non-Windows, use standard stdout
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