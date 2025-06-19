"""
Qt Warning Suppression
Filters out common Qt warnings that clutter the console
"""

import warnings
import logging

def suppress_qt_warnings():
    """Suppress common Qt warnings that can't be fixed easily"""
    
    # Suppress Qt warnings about CSS properties
    warnings.filterwarnings("ignore", message="Unknown property")
    warnings.filterwarnings("ignore", message="QPropertyAnimation")
    
    # Also suppress via logging
    logging.getLogger("PySide6").setLevel(logging.ERROR)
    logging.getLogger("Qt").setLevel(logging.ERROR)
    
    # Suppress specific Qt messages
    import os
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false;qt.qpa.gl.warning=false"
    
def setup_qt_message_handler():
    """Install custom Qt message handler to filter warnings"""
    from PySide6.QtCore import qInstallMessageHandler, QtMsgType
    
    def qt_message_handler(msg_type, context, msg):
        # Filter out specific messages
        if msg_type == QtMsgType.QtWarningMsg:
            # Ignore CSS warnings
            if any(x in msg for x in ["Unknown property", "box-shadow", "content", "QPropertyAnimation"]):
                return
        
        # Let other messages through
        if msg_type == QtMsgType.QtCriticalMsg:
            print(f"Qt Critical: {msg}")
        elif msg_type == QtMsgType.QtFatalMsg:
            print(f"Qt Fatal: {msg}")
        # Suppress info and debug messages
    
    qInstallMessageHandler(qt_message_handler)