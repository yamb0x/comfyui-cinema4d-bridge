"""
Application styling and themes
"""

from .styles_new import get_monospace_stylesheet

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
    """Black theme based on the HTML redesign"""
    return f"""
        /* Base Application Style */
        QMainWindow {{
            background-color: #000000;
            color: #ffffff;
            font-family: 'Basis Grotesque', monospace;
            font-size: 11px;
        }}
        
        /* Header Styling */
        QWidget#main_header {{
            background-color: #000000;
            border-bottom: 1px solid #333333;
            min-height: 60px;
            max-height: 60px;
        }}
        
        QLabel#main_title {{
            font-family: 'Kalice', serif;
            font-size: 16px;
            font-weight: 400;
            letter-spacing: 0.3px;
            color: #ffffff;
            min-height: 20px;
            max-height: 20px;
            padding: 0px;
            margin: 0px;
        }}
        
        QLabel#main_subtitle {{
            font-family: 'Basis Grotesque', monospace;
            font-size: 9px;
            color: #666666;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            min-height: 12px;
            max-height: 12px;
            padding: 0px;
            margin: 0px;
        }}
        
        /* Status Indicators */
        QLabel#status_circle_connected {{
            color: #4CAF50;
            font-size: 12px;
            font-weight: bold;
        }}
        
        QLabel#status_circle_disconnected {{
            color: #ff4444;
            font-size: 12px;
            font-weight: bold;
        }}
        
        QLabel#status_text {{
            font-family: 'Basis Grotesque', monospace;
            color: #ffffff;
            font-size: 11px;
            font-weight: 500;
        }}
        
        QLabel#connection_info {{
            font-family: 'Basis Grotesque', monospace;
            color: #666666;
            font-size: 9px;
            font-weight: 400;
        }}
        
        /* Panel Styling */
        QGroupBox {{
            background-color: #000000;
            border: 1px solid #333333;
            font-size: 10px;
            font-weight: 600;
            color: #999999;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            padding-top: 12px;
            border-radius: 0px;
        }}
        
        QGroupBox#panel_header {{
            background-color: #000000;
            border-bottom: 1px solid #333333;
            padding: 10px 12px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 5px 0 5px;
            color: #999999;
        }}
        
        /* Ensure all widgets inside panels use dark background */
        QWidget {{
            background-color: #000000;
            color: #ffffff;
        }}
        
        /* Parameter sections specifically */
        QWidget#parameter_section {{
            background-color: #000000;
            border-bottom: 1px solid #333333;
        }}
        
        /* Content areas and scroll areas */
        QScrollArea {{
            background-color: #000000;
            border: none;
        }}
        
        QScrollArea > QWidget > QWidget {{
            background-color: #000000;
        }}
        
        /* Object Generation Preview Container */
        QWidget#object_preview_container {{
            background-color: #111111;
            border: 1px solid #333333;
            padding: 15px;
        }}
        
        /* Tab Styling */
        QTabWidget::pane {{
            border: none;
            background-color: #0a0a0a;
        }}
        
        QTabWidget::tab-bar {{
            alignment: left;
        }}
        
        QTabBar::tab {{
            background-color: #1a1a1a;
            color: #888888;
            padding: 10px 18px;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid transparent;
            margin-right: 0px;
            border-radius: 0px;
        }}
        
        QTabBar::tab:selected {{
            color: #ffffff;
            border-bottom: 2px solid #ffffff;
            background-color: rgba(255,255,255,0.05);
        }}
        
        QTabBar::tab:hover:!selected {{
            color: #bbbbbb;
            background-color: rgba(255,255,255,0.02);
        }}
        
        /* Input Controls with Grid Layout */
        QLineEdit, QTextEdit, QComboBox {{
            background-color: #222222;
            border: 1px solid #444444;
            color: #ffffff;
            padding: 6px 8px;
            font-size: 11px;
            font-family: inherit;
            border-radius: 0px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border-color: #888888;
            background-color: #2a2a2a;
            outline: none;
        }}
        
        QLineEdit:hover, QTextEdit:hover, QComboBox:hover {{
            border-color: #666666;
        }}
        
        /* Spinbox with Custom Arrows */
        QSpinBox, QDoubleSpinBox {{
            background-color: #222222;
            border: 1px solid #444444;
            color: #ffffff;
            padding: 4px 6px;
            font-size: 10px;
            min-width: 60px;
            border-radius: 0px;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: #888888;
            background-color: #2a2a2a;
        }}
        
        QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: #666666;
        }}
        
        /* Custom smaller arrows for spinboxes */
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 12px;
            height: 8px;
            border-left: 1px solid #444444;
            background-color: #333333;
        }}
        
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background-color: #555555;
        }}
        
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-bottom: 4px solid #cccccc;
        }}
        
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 12px;
            height: 8px;
            border-left: 1px solid #444444;
            background-color: #333333;
        }}
        
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: #555555;
        }}
        
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-top: 4px solid #cccccc;
        }}
        
        /* Button Styling */
        QPushButton#generate_btn {{
            background-color: #ffffff;
            color: #000000;
            border: none;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: 500;
            font-family: inherit;
            border-radius: 0px;
        }}
        
        QPushButton#generate_btn:hover {{
            background-color: #f0f0f0;
        }}
        
        QPushButton#secondary_btn {{
            background-color: transparent;
            color: #cccccc;
            border: 1px solid #444444;
            padding: 8px 12px;
            font-size: 11px;
            font-family: inherit;
            border-radius: 0px;
        }}
        
        QPushButton#secondary_btn:hover {{
            border-color: #666666;
            color: #ffffff;
            background-color: #222222;
        }}
        
        /* Labels and Text */
        QLabel#section_title {{
            font-family: 'Basis Grotesque', monospace;
            font-size: 10px;
            color: #aaaaaa;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
            margin-bottom: 2px;
        }}
        
        QLabel#panel_subtitle {{
            font-family: 'Basis Grotesque', monospace;
            font-size: 10px;
            color: #aaaaaa;
        }}
        
        /* Content Areas */
        QWidget#content_area {{
            background-color: #0a0a0a;
        }}
        
        /* Console Styling */
        QWidget#console_group {{
            background-color: #000000;
            border-top: 1px solid #333333;
        }}
        
        QTextEdit#console {{
            background-color: #000000;
            color: #4CAF50;
            font-family: monospace;
            font-size: 9px;
            border: none;
        }}
        
        /* Checkbox Styling */
        QCheckBox {{
            font-family: 'Basis Grotesque', monospace;
            color: #cccccc;
            font-size: 11px;
        }}
        
        QCheckBox::indicator {{
            width: 12px;
            height: 12px;
            background-color: #222222;
            border: 1px solid #444444;
        }}
        
        QCheckBox::indicator:checked {{
            background-color: #4CAF50;
            border-color: #4CAF50;
        }}
        
        /* Scrollbar Styling */
        QScrollBar:vertical {{
            background-color: #222222;
            width: 8px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: #555555;
            border-radius: 4px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: #777777;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        /* Grid layout helpers */
        QWidget#parameter_section {{
            border-bottom: 1px solid #333333;
        }}
        
        /* ComboBox dropdown styling */
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
            border-left: 1px solid #444444;
            background-color: #333333;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #cccccc;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: #222222;
            border: 1px solid #444444;
            selection-background-color: #555555;
            color: #ffffff;
        }}
    """

def get_available_themes() -> dict:
    """Get available theme options"""
    return {
        "dark": get_dark_stylesheet,
        "monospace": get_monospace_stylesheet,
        "black": get_black_theme,
        "light": get_light_stylesheet
    }