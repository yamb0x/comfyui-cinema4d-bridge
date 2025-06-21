#!/usr/bin/env python3
"""
comfy2c4d - AI to 3D Workflow Integration
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

from core.app_redesigned import ComfyToC4DAppRedesigned as ComfyToC4DApp
from core.config_adapter import AppConfig
from utils.logger import setup_logging
from utils.qt_warnings import suppress_qt_warnings, setup_qt_message_handler


async def main():
    """Main application entry point"""
    # Setup logging with reduced verbosity
    setup_logging(debug=False)
    logger.info("Starting comfy2c4d Application")
    
    # Suppress Qt warnings
    suppress_qt_warnings()
    
    # Load configuration
    config = AppConfig.load()
    
    # Create Qt Application
    app = QApplication(sys.argv)
    
    # Setup Qt message handler to filter warnings
    setup_qt_message_handler()
    app.setApplicationName("ComfyUI to Cinema4D Bridge")
    app.setOrganizationName("Yambo Studio")
    
    # Enable high DPI support (Qt6 way - the old attributes are deprecated)
    # Qt6 handles high DPI automatically, no need to set these deprecated attributes
    
    # Create main application window
    main_window = ComfyToC4DApp(config)
    main_window.show()
    
    # Setup async event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Initialize application using async task
    async def init_app():
        await main_window.initialize()
    
    # Schedule initialization
    asyncio.ensure_future(init_app())
    
    # Run the application
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    # Enable fault handler for better crash debugging
    import faulthandler
    faulthandler.enable()
    
    # Set up exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)