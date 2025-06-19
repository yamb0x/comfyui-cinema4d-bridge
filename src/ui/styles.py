"""
Application styling and themes
"""

from .styles_new import get_monospace_stylesheet
from .terminal_theme import get_terminal_theme

def get_dark_stylesheet() -> str:
    """Get dark theme stylesheet"""
    return """
    /* Main application */
    QMainWindow {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    
    QWidget {
        background-color: #2a2a2a;
        color: #e0e0e0;
    }
    
    /* Group boxes */
    QGroupBox {
        background-color: #252525;
        border: 1px solid #3a3a3a;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
        font-weight: bold;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        color: #4CAF50;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #3a3a3a;
        border: 1px solid #4a4a4a;
        border-radius: 4px;
        padding: 5px 15px;
        color: #e0e0e0;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #4a4a4a;
    }
        border-color: #5a5a5a;
    }
    
    QPushButton:pressed {
        background-color: #2a2a2a;
    }
    
    QPushButton:checked {
        background-color: #4CAF50;
        color: white;
    }
    
    QPushButton:disabled {
        background-color: #2a2a2a;
        color: #666;
        border-color: #3a3a3a;
    }
    
    /* Primary action buttons */
    QPushButton#generate_btn,
    QPushButton#generate_3d_btn,
    QPushButton#import_selected_btn,
    QPushButton#export_btn {
        background-color: #4CAF50;
        color: white;
        font-size: 14px;
        padding: 8px 20px;
    }
    
    QPushButton#generate_btn:hover,
    QPushButton#generate_3d_btn:hover,
    QPushButton#import_selected_btn:hover,
    QPushButton#export_btn:hover {
        background-color: #5CBF60;
    }
    
    /* Input widgets */
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background-color: #1a1a1a;
        border: 1px solid #3a3a3a;
        border-radius: 4px;
        padding: 5px;
        color: #e0e0e0;
    }
    
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, 
    QDoubleSpinBox:focus, QComboBox:focus {
        border-color: #4CAF50;
        outline: none;
    }
    
    /* Combo box */
    QComboBox::drop-down {
        border-left: 1px solid #3a3a3a;
        width: 20px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-style: solid;
        border-width: 5px;
        border-color: transparent;
        border-top-color: #e0e0e0;
        margin-top: 2px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #2a2a2a;
        border: 1px solid #3a3a3a;
        selection-background-color: #4CAF50;
    }
    
    /* Spin boxes */
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        border-left: 1px solid #3a3a3a;
        width: 16px;
        background-color: #3a3a3a;
    }
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        border-left: 1px solid #3a3a3a;
        width: 16px;
        background-color: #3a3a3a;
    }
    
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        image: none;
        border-style: solid;
        border-width: 4px;
        border-color: transparent;
        border-bottom-color: #e0e0e0;
    }
    
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        image: none;
        border-style: solid;
        border-width: 4px;
        border-color: transparent;
        border-top-color: #e0e0e0;
    }
    
    /* Check boxes */
    QCheckBox {
        spacing: 5px;
    }
    
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        background-color: #1a1a1a;
        border: 1px solid #3a3a3a;
        border-radius: 3px;
    }
    
    QCheckBox::indicator:checked {
        background-color: #4CAF50;
        border-color: #4CAF50;
    }
    
    QCheckBox::indicator:checked:after {
        content: "";
        position: absolute;
        width: 10px;
        height: 6px;
        border: 2px solid white;
        border-top: none;
        border-right: none;
        transform: rotate(-45deg);
        left: 2px;
        top: 3px;
    }
    
    /* Lists and tables */
    QListWidget, QTableWidget {
        background-color: #1a1a1a;
        border: 1px solid #3a3a3a;
        border-radius: 4px;
        alternate-background-color: #252525;
    }
    
    QListWidget::item, QTableWidget::item {
        padding: 5px;
        border-bottom: 1px solid #2a2a2a;
    }
    
    QListWidget::item:selected, QTableWidget::item:selected {
        background-color: #4CAF50;
        color: white;
    }
    
    QListWidget::item:hover, QTableWidget::item:hover {
        background-color: #3a3a3a;
    }
    
    /* Headers */
    QHeaderView::section {
        background-color: #2a2a2a;
        color: #e0e0e0;
        padding: 5px;
        border: none;
        border-right: 1px solid #3a3a3a;
        border-bottom: 1px solid #3a3a3a;
        font-weight: bold;
    }
    
    /* Scroll bars */
    QScrollBar:vertical {
        background-color: #1a1a1a;
        width: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #4a4a4a;
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #5a5a5a;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    
    QScrollBar:horizontal {
        background-color: #1a1a1a;
        height: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #4a4a4a;
        border-radius: 6px;
        min-width: 20px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #5a5a5a;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    
    /* Splitters */
    QSplitter::handle {
        background-color: #3a3a3a;
    }
    
    QSplitter::handle:horizontal {
        width: 4px;
    }
    
    QSplitter::handle:vertical {
        height: 4px;
    }
    
    /* Tab widget */
    QTabWidget::pane {
        background-color: #2a2a2a;
        border: 1px solid #3a3a3a;
    }
    
    QTabBar::tab {
        background-color: #2a2a2a;
        color: #e0e0e0;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #3a3a3a;
        color: #4CAF50;
    }
    
    QTabBar::tab:hover {
        background-color: #353535;
    }
    
    /* Progress bar */
    QProgressBar {
        background-color: #1a1a1a;
        border: 1px solid #3a3a3a;
        border-radius: 4px;
        text-align: center;
        color: white;
    }
    
    QProgressBar::chunk {
        background-color: #4CAF50;
        border-radius: 3px;
    }
    
    /* Status bar */
    QStatusBar {
        background-color: #1a1a1a;
        color: #e0e0e0;
        border-top: 1px solid #3a3a3a;
    }
    
    /* Labels */
    QLabel {
        color: #e0e0e0;
    }
    
    /* Frames */
    QFrame[frameShape="4"] {  /* HLine */
        background-color: #3a3a3a;
        max-height: 1px;
    }
    
    QFrame[frameShape="5"] {  /* VLine */
        background-color: #3a3a3a;
        max-width: 1px;
    }
    
    /* Tool tips */
    QToolTip {
        background-color: #3a3a3a;
        color: #e0e0e0;
        border: 1px solid #4a4a4a;
        padding: 5px;
        border-radius: 4px;
    }
    
    /* Message boxes */
    QMessageBox {
        background-color: #2a2a2a;
        color: #e0e0e0;
    }
    
    QMessageBox QPushButton {
        min-width: 80px;
    }
    
    /* Chat Interface Styles */
    QWidget#chat_header {
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
        padding: 10px;
    }
    
    QWidget#chat_status {
        font-size: 12px;
        color: #888888;
        padding: 10px;
    }
    
    QTextEdit#chat_history {
        background-color: #1a1a1a;
        color: #e0e0e0;
        border: none;
        font-family: 'Inter', 'SF Pro', -apple-system, sans-serif;
        font-size: 14px;
        padding: 10px;
        line-height: 1.6;
    }
    
    QTextEdit#chat_input {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #4a4a4a;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
    }
    
    QTextEdit#chat_input:focus {
        border-color: #0084ff;
    }
    
    QPushButton#send_btn {
        background-color: #0084ff;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 20px;
        min-width: 40px;
        min-height: 40px;
        max-width: 40px;
        max-height: 40px;
    }
    
    QPushButton#send_btn:hover {
        background-color: #0073e6;
    }
    
    QPushButton#send_btn:disabled {
        background-color: #4a4a4a;
    }
    
    QToolButton#attach_btn {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 2px dashed #4a4a4a;
        border-radius: 8px;
        font-size: 20px;
        min-width: 40px;
        min-height: 40px;
        max-width: 40px;
        max-height: 40px;
    }
    
    QToolButton#attach_btn:hover {
        background-color: #3d3d3d;
        border-color: #6a6a6a;
    }
    
    /* Knowledge Dictionary Styles */
    QLabel#dict_header {
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
        padding: 10px;
        background-color: #2d2d2d;
        border-radius: 8px;
    }
    
    QLineEdit#search_input {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #4a4a4a;
        border-radius: 6px;
        padding: 8px;
        font-size: 14px;
    }
    
    QScrollArea#dict_scroll {
        background-color: #1a1a1a;
        border: none;
    }
    
    QPushButton#section_header {
        background-color: #2d2d2d;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 10px;
        text-align: left;
        font-size: 16px;
        font-weight: bold;
    }
    
    QPushButton#section_header:hover {
        background-color: #3d3d3d;
    }
    
    QWidget#section_content {
        background-color: #262626;
        border-radius: 6px;
        margin-top: 2px;
    }
    
    QPushButton#example_item {
        background-color: transparent;
        color: #e0e0e0;
        border: none;
        padding: 5px 20px;
        text-align: left;
        font-size: 14px;
    }
    
    QPushButton#example_item:hover {
        background-color: #2d2d2d;
        color: #0084ff;
    }
    
    QLabel#examples_label {
        color: #888888;
        font-weight: bold;
        padding: 5px;
    }
    
    QLabel#keywords_label {
        color: #0084ff;
        padding: 5px;
        font-size: 13px;
    }
    
    QLabel#capabilities_label {
        color: #888888;
        font-weight: bold;
        padding: 5px 5px 0 5px;
    }
    
    QLabel#capabilities_text {
        color: #cccccc;
        padding: 2px 5px 5px 20px;
        font-size: 13px;
    }
    
    QLabel#tips_label {
        color: #888888;
        font-size: 12px;
        padding: 10px;
        background-color: #2d2d2d;
        border-radius: 6px;
        margin-top: 5px;
    }
    
    /* Test Controls Styles */
    QGroupBox#test_controls {
        background-color: #2d2d2d;
        border: 1px solid #4a4a4a;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        font-weight: bold;
    }
    
    QPushButton#test_btn {
        background-color: #3d3d3d;
        color: #ffffff;
        border: 1px solid #4a4a4a;
        border-radius: 4px;
        padding: 8px;
        font-size: 12px;
        min-height: 30px;
    }
    
    QPushButton#test_btn:hover {
        background-color: #4d4d4d;
        border-color: #5a5a5a;
    }
    
    QPushButton#test_btn:pressed {
        background-color: #2d2d2d;
    }
    
    /* Separator styling */
    QFrame#separator {
        background-color: #3a3a3a;
        max-height: 1px;
        margin: 5px 0;
    }
    """


def get_light_stylesheet() -> str:
    """Get light theme stylesheet"""
    return """
    /* Light theme - to be implemented */
    QMainWindow {
        background-color: #f5f5f5;
        color: #333333;
    }
    """


def get_black_theme():
    """Terminal theme based on the professional monospace design"""
    return get_terminal_theme()

def get_available_themes() -> dict:
    """Get available theme options"""
    return {
        "dark": get_dark_stylesheet,
        "monospace": get_monospace_stylesheet,
        "black": get_black_theme,
        "light": get_light_stylesheet
    }