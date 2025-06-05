#!/usr/bin/env python3
"""
ComfyUI to Cinema4D Bridge Application
Main entry point for the desktop application
"""

import sys
import asyncio
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qasync import QEventLoop, asyncSlot
from loguru import logger

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.app import ComfyToC4DApp
from core.config_adapter import AppConfig
from utils.logger import setup_logging


async def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger.info("Starting ComfyUI to Cinema4D Bridge Application")
    
    # Load configuration
    config = AppConfig.load()
    
    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("ComfyUI to Cinema4D Bridge")
    app.setOrganizationName("Yambo Studio")
    
    # Enable high DPI support
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create main application window
    main_window = ComfyToC4DApp(config)
    main_window.show()
    
    # Setup async event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Initialize application
    await main_window.initialize()
    
    # Run the application
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)