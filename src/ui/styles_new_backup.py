"""
New monospace-inspired UI styles
Based on monospace web design principles and user design reference
"""

def get_monospace_stylesheet() -> str:
    """Get clean monospace-inspired stylesheet"""
    return """
    /* Monospace-inspired theme with clean white background */
    /* Qt doesn't support CSS variables, using direct values */

    /* Main application window */
    QMainWindow {
        background-color: #ffffff;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', 'Helvetica Neue', sans-serif;
        font-size: 14px;
    }
    
    QWidget {
        background-color: #ffffff;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', 'Helvetica Neue', sans-serif;
    }

    /* Main header - exactly like reference */
    QWidget[objectName="main_header"] {
        background-color: #000000;
        color: #ffffff;
        border-bottom: 1px solid #000000;
    }

    QLabel[objectName="main_title"] {
        background-color: transparent;
        color: #ffffff;
        font-family: 'Kalice', 'Georgia', 'Times New Roman', serif;
        font-size: 24px;
        font-weight: normal;
        padding: 0px;
        margin: 0px;
    }

    QLabel[objectName="main_subtitle"] {
        background-color: transparent;
        color: #ffffff;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        opacity: 0.7;
        padding: 0px;
        margin: 0px;
    }

    /* Panel headers - fixed overlapping and consistent fonts */
    QGroupBox[objectName="panel_header"] {
        background-color: #ffffff;
        border: none;
        border-bottom: 1px solid #000000;
        margin: 0px;
        padding-top: 25px;
        font-family: 'Kalice', 'Georgia', 'Times New Roman', serif;
        font-size: 18px;
        font-weight: normal;
    }

    QGroupBox[objectName="panel_header"]::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 20px;
        padding: 5px 10px;
        background-color: #ffffff;
        color: #000000;
        font-family: 'Kalice', 'Georgia', 'Times New Roman', serif;
        font-size: 18px;
        font-weight: normal;
        margin-bottom: 4px;
    }

    /* Group boxes with consistent styling */
    QGroupBox {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        margin-top: 15px;
        padding-top: 20px;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 12px;
        font-weight: bold;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 10px;
        background-color: #ffffff;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Buttons - consistent fonts and styling */
    QPushButton {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        padding: 10px 16px;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        min-height: 20px;
    }
    
    QPushButton:hover {
        background-color: #000000;
        color: #ffffff;
    }
    
    QPushButton:pressed {
        background-color: #666666;
        color: #ffffff;
    }
    
    QPushButton:checked {
        background-color: #000000;
        color: #ffffff;
    }
    
    QPushButton:disabled {
        background-color: #f8f8f8;
        color: #666666;
        border-color: #666666;
    }

    /* Primary buttons */
    QPushButton[objectName="generate_btn"],
    QPushButton[objectName="generate_3d_btn"],
    QPushButton[objectName="import_selected_btn"],
    QPushButton[objectName="export_btn"] {
        background-color: #000000;
        color: #ffffff;
        font-weight: bold;
        padding: 12px 20px;
        font-size: 14px;
    }
    
    QPushButton[objectName="generate_btn"]:hover,
    QPushButton[objectName="generate_3d_btn"]:hover,
    QPushButton[objectName="import_selected_btn"]:hover,
    QPushButton[objectName="export_btn"]:hover {
        background-color: #666666;
    }

    /* Input fields - consistent fonts */
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        padding: 8px 12px;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 13px;
    }
    
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #000000;
        border-width: 2px;
    }

    /* Prompt input areas */
    QTextEdit[objectName="prompt_input"] {
        min-height: 120px;
        font-size: 13px;
        line-height: 1.6;
    }

    /* ComboBox - consistent fonts */
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        padding: 10px 12px;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 13px;
        min-height: 20px;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 30px;
        background: #ffffff;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #000000;
        margin-right: 8px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #000000;
        selection-background-color: #000000;
        selection-color: #ffffff;
    }

    /* Checkboxes - consistent fonts */
    QCheckBox {
        spacing: 8px;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 13px;
    }
    
    QCheckBox::indicator {
        width: 14px;
        height: 14px;
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
    }
    
    QCheckBox::indicator:checked {
        background-color: #000000;
        border-color: #000000;
    }

    /* List widgets and tables - consistent fonts */
    QListWidget, QTableWidget {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        alternate-background-color: #f8f8f8;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 13px;
    }
    
    QListWidget::item, QTableWidget::item {
        padding: 12px;
        border-bottom: 1px solid #000000;
        background-color: #ffffff;
    }
    
    QListWidget::item:selected, QTableWidget::item:selected {
        background-color: #000000;
        color: #ffffff;
    }
    
    QListWidget::item:hover, QTableWidget::item:hover {
        background-color: #f8f8f8;
    }

    /* Headers */
    QHeaderView::section {
        background-color: #ffffff;
        color: #000000;
        padding: 8px;
        border: none;
        border-right: 1px solid #000000;
        border-bottom: 1px solid #000000;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 11px;
    }

    /* Scroll bars - minimal */
    QScrollBar:vertical {
        background-color: #f8f8f8;
        width: 8px;
        border-radius: 0px;
        border: none;
    }
    
    QScrollBar::handle:vertical {
        background-color: #666666;
        border-radius: 0px;
        min-height: 20px;
        border: none;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #000000;
    }

    /* Connection status indicators */
    QLabel[objectName="status_connected"] {
        color: #000000;
        font-weight: bold;
    }
    
    QLabel[objectName="status_disconnected"] {
        color: #666666;
    }
    
    QLabel[objectName="status_error"] {
        color: #ff0000;
    }

    /* Console widget - clean white with monospace */
    QTextEdit[objectName="console"] {
        background-color: #ffffff;
        border: none;
        color: #000000;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 12px;
        padding: 15px;
        line-height: 1.4;
    }
    
    /* Console group box */
    QGroupBox[objectName="console_group"] {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        margin: 0px;
        padding: 0px;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-weight: bold;
    }
    
    QGroupBox[objectName="console_group"]::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 10px;
        background-color: #ffffff;
        color: #000000;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Progress bar */
    QProgressBar {
        background-color: #f8f8f8;
        border: 1px solid #000000;
        border-radius: 0px;
        text-align: center;
        color: #000000;
        font-size: 11px;
        font-weight: bold;
        padding: 2px;
    }
    
    QProgressBar::chunk {
        background-color: #000000;
        border-radius: 0px;
    }

    /* Status bar */
    QStatusBar {
        background-color: #ffffff;
        color: #000000;
        border-top: 1px solid #000000;
        padding: 5px;
    }

    /* Tab widget */
    QTabWidget::pane {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
    }
    
    QTabBar::tab {
        background-color: #ffffff;
        color: #000000;
        padding: 12px 20px;
        margin-right: 1px;
        border: 1px solid #000000;
        border-bottom: none;
        font-size: 12px;
        text-transform: uppercase;
    }
    
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #000000;
        border-bottom: 1px solid #ffffff;
    }
    
    QTabBar::tab:hover {
        background-color: #f8f8f8;
    }

    /* Tool tips */
    QToolTip {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #000000;
        padding: 8px;
        border-radius: 0px;
        font-size: 12px;
    }

    /* Pipeline status area - matching reference design */
    QWidget[objectName="pipeline_status"] {
        background-color: #ffffff;
        border-bottom: 1px solid #000000;
        padding: 20px;
        min-height: 80px;
    }

    /* Pipeline step indicators - exactly like reference */
    QPushButton[objectName="stage_indicator"] {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
    }

    QPushButton[objectName="stage_indicator"]:checked {
        background-color: #000000;
        color: #ffffff;
    }

    QPushButton[objectName="stage_indicator"]:hover {
        background-color: #f8f8f8;
    }

    QPushButton[objectName="stage_indicator"]:checked:hover {
        background-color: #333333;
    }

    /* Section titles - matching reference design */
    QLabel[objectName="section_title"] {
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #666666;
        font-weight: bold;
        margin-bottom: 12px;
        padding: 0px;
    }

    /* Content areas with proper spacing */
    QWidget[objectName="content_area"] {
        background-color: #f8f8f8;
        padding: 20px;
    }

    /* Model preview cards - better spacing */
    QFrame[objectName="model_preview"] {
        background-color: #ffffff;
        border: 1px solid #000000;
        padding: 15px;
        margin: 10px;
        min-width: 280px;
    }

    /* Model viewport styling */
    QLabel[objectName="model_viewport"] {
        background-color: #f0f0f0;
        border: 1px solid #000000;
        min-height: 200px;
        text-align: center;
        color: #666666;
        font-size: 12px;
    }

    /* Parameter controls - clean styling without borders */
    QWidget[objectName="parameter_section"] {
        background-color: #ffffff;
        border: none;
        padding: 20px;
        margin-bottom: 15px;
    }

    /* Object count inputs - smaller and cleaner */
    QSpinBox[objectName="object_count"] {
        max-width: 50px;
        min-width: 50px;
        padding: 4px 6px;
        text-align: center;
        font-weight: normal;
        font-size: 12px;
        border: 1px solid #000000;
        background-color: #ffffff;
    }
    
    QSpinBox[objectName="object_count"]::up-button,
    QSpinBox[objectName="object_count"]::down-button {
        width: 12px;
        border: none;
        background: #ffffff;
    }
    
    QSpinBox[objectName="object_count"]::up-arrow {
        image: none;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-bottom: 4px solid #000000;
    }
    
    QSpinBox[objectName="object_count"]::down-arrow {
        image: none;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-top: 4px solid #000000;
    }
    """