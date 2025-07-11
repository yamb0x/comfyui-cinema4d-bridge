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

    /* Group boxes with consistent styling - no overlapping borders */
    QGroupBox {
        background-color: #ffffff;
        border: none;
        border-radius: 0px;
        margin-top: 15px;
        padding-top: 20px;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 12px;
        font-weight: bold;
    }
    
    /* Only specific group boxes get borders */
    QGroupBox[objectName="console_group"] {
        border: 1px solid #000000;
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
        font-size: 13px;
        line-height: 1.6;
        padding: 4px 8px;
        margin: 0px;
    }
    
    /* All QTextEdit in parameter sections - tight spacing */
    QWidget[objectName="parameter_section"] QTextEdit {
        padding: 4px 8px;
        margin: 0px;
    }
    
    /* Prompt sections - ultra tight spacing */
    QWidget[objectName="prompt_section"] {
        background-color: #ffffff;
        border: none;
        padding: 0px;
        margin: 0px;
    }
    
    QWidget[objectName="prompt_section"] QTextEdit {
        padding: 4px 8px;
        margin: 0px;
    }
    
    QWidget[objectName="prompt_section"] QLabel[objectName="section_title"] {
        margin-bottom: 2px;
        margin-top: 0px;
        padding: 0px;
    }

    /* ComboBox - consistent fonts and clear styling */
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        padding: 8px 12px;
        color: #000000;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 13px;
        min-height: 18px;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 25px;
        background: #ffffff;
        subcontrol-origin: padding;
        subcontrol-position: right;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #000000;
        margin-right: 6px;
    }
    
    QComboBox:hover {
        border-color: #333333;
    }
    
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #000000;
        selection-background-color: #000000;
        selection-color: #ffffff;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 13px;
        outline: none;
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

    /* Console widget - clean white with colored text */
    QTextEdit[objectName="console"] {
        background-color: #ffffff;
        border: none;
        color: #333333;
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

    /* Section titles - removed duplicate, using better alignment version below */

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
        min-width: 150px;  /* Reduced for more compact panels */
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
        padding: 0px;
        margin: 0px;
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

    /* Connection info styling */
    QLabel[objectName="connection_info"] {
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 10px;
        color: #666666;
        padding: 0px;
        margin: 0px;
    }

    /* Panel subtitle styling */
    QLabel[objectName="panel_subtitle"] {
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 12px;
        color: #666666;
        margin: 0px;
        padding: 0px;
    }

    /* Image placeholder styling */
    QWidget[objectName="image_slot"] {
        background-color: #f0f0f0;
        border: 1px solid #000000;
        border-radius: 0px;
    }
    
    /* 3D Model card styling - matches image cards */
    QWidget[objectName="model_slot"] {
        background-color: #f0f0f0;
        border: 1px solid #000000;
        border-radius: 0px;
    }

    QLabel[objectName="image_placeholder"] {
        background-color: transparent;
        color: #666666;
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 12px;
        text-align: center;
        padding: 20px;
    }

    /* Responsive design improvements */
    QSplitter::handle {
        background: #000000;
        width: 1px;
        height: 1px;
    }

    QSplitter::handle:horizontal {
        width: 1px;
    }

    QSplitter::handle:vertical {
        height: 1px;
    }

    /* Improved scrollbar for larger content */
    QScrollArea {
        border: none;
        background-color: #ffffff;
    }

    QScrollArea > QWidget > QWidget {
        background-color: #ffffff;
    }

    /* Magic button inside prompt */
    QPushButton[objectName="magic_btn"] {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        padding: 2px;
        color: #000000;
        font-size: 12px;
        margin: 2px;
    }
    
    QPushButton[objectName="magic_btn"]:hover {
        background-color: #000000;
        color: #ffffff;
    }

    /* Action buttons for images - larger buttons */
    QPushButton[objectName="action_btn"] {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        padding: 4px;
        color: #000000;
        font-size: 14px;
        font-weight: normal;
    }
    
    QPushButton[objectName="action_btn"]:hover {
        background-color: #f8f8f8;
    }
    
    QPushButton[objectName="action_btn_primary"] {
        background-color: #000000;
        border: 1px solid #000000;
        border-radius: 0px;
        padding: 4px;
        color: #ffffff;
        font-size: 14px;
        font-weight: bold;
    }
    
    QPushButton[objectName="action_btn_primary"]:hover {
        background-color: #333333;
    }

    /* Image slots - larger size */
    QWidget[objectName="image_slot"] {
        background-color: #f8f8f8;
        border: 1px solid #000000;
        border-radius: 0px;
        margin: 0px;
    }

    /* Better alignment for titles */
    QLabel[objectName="section_title"] {
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #666666;
        font-weight: bold;
        margin-bottom: 4px;
        margin-left: 2px;
        padding: 0px;
    }

    /* Connection status improvements */
    QLabel[objectName="connection_info"] {
        font-family: 'Basis Grotesque', 'Arial', sans-serif;
        font-size: 9px;
        color: #999999;
        padding: 0px;
        margin: 0px;
    }

    /* ===== CINEMA4D TRAINING INTERFACE STYLES ===== */
    
    QGroupBox[objectName="training_header"] {
        font-weight: bold;
        color: #000000;
        border: 2px solid #000000;
        border-radius: 4px;
        margin-top: 10px;
        padding-top: 10px;
    }
    
    QGroupBox[objectName="training_header"]::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
        color: #000000;
        font-weight: bold;
    }
    
    QLabel[objectName="stage_info"] {
        color: #000000;
        font-weight: bold;
        font-size: 13px;
    }
    
    QLabel[objectName="intelligence_info"] {
        color: #666666;
        font-size: 13px;
    }
    
    QLabel[objectName="progress_info"] {
        color: #666666;
        font-size: 12px;
        font-style: italic;
    }
    
    QLabel[objectName="intelligence_target"] {
        color: #333333;
        font-size: 12px;
        font-weight: bold;
    }
    
    QTabWidget[objectName="training_tabs"] {
        border: 1px solid #e1e1e1;
    }
    
    QTabWidget[objectName="training_tabs"]::pane {
        border: 1px solid #e1e1e1;
        background-color: #ffffff;
    }
    
    QTabWidget[objectName="training_tabs"]::tab-bar {
        alignment: left;
    }
    
    QTabBar::tab {
        background-color: #f5f5f5;
        color: #666666;
        border: 1px solid #e1e1e1;
        border-bottom: none;
        padding: 6px 12px;
        margin-right: 2px;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #000000;
        font-weight: bold;
        border-bottom: 1px solid #ffffff;
    }
    
    QTabBar::tab:hover {
        background-color: #e8e8e8;
        color: #333333;
    }
    
    /* Training button styles */
    QPushButton[objectName="tiny_btn"] {
        background-color: #f5f5f5;
        color: #666666;
        border: 1px solid #e1e1e1;
        border-radius: 3px;
        padding: 3px 6px;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        min-height: 20px;
        max-height: 24px;
    }
    
    QPushButton[objectName="tiny_btn"]:hover {
        background-color: #e8e8e8;
        color: #333333;
        border-color: #cccccc;
    }
    
    QPushButton[objectName="tiny_btn"]:pressed {
        background-color: #000000;
        color: #ffffff;
        border-color: #000000;
    }
    
    QPushButton[objectName="hierarchy_btn"] {
        background-color: #ffffff;
        color: #000000;
        border: 2px solid #000000;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    QPushButton[objectName="hierarchy_btn"]:hover {
        background-color: #000000;
        color: #ffffff;
    }
    
    QPushButton[objectName="workflow_btn"] {
        background-color: #f5f5f5;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 10px 16px;
        font-size: 12px;
        font-weight: bold;
    }
    
    QPushButton[objectName="workflow_btn"]:hover {
        background-color: #e8e8e8;
        border-color: #999999;
    }
    
    QPushButton[objectName="workflow_btn"]:pressed {
        background-color: #cccccc;
        border-color: #666666;
    }
    
    QPushButton[objectName="nl_test_btn"] {
        background-color: #000000;
        color: #ffffff;
        border: 2px solid #000000;
        border-radius: 4px;
        padding: 10px 16px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    QPushButton[objectName="nl_test_btn"]:hover {
        background-color: #333333;
        border-color: #333333;
    }
    
    QPushButton[objectName="test_btn"] {
        background-color: #666666;
        color: #ffffff;
        border: 1px solid #666666;
        border-radius: 3px;
        padding: 6px 12px;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    QPushButton[objectName="test_btn"]:hover {
        background-color: #333333;
        border-color: #333333;
    }
    
    QPushButton[objectName="connection_test_btn"] {
        background-color: #f5f5f5;
        color: #666666;
        border: 1px solid #e1e1e1;
        border-radius: 3px;
        padding: 6px 12px;
        font-size: 11px;
    }
    
    QPushButton[objectName="connection_test_btn"]:hover {
        background-color: #e8e8e8;
        color: #333333;
    }
    
    QPushButton[objectName="import_btn"] {
        background-color: #ffffff;
        color: #000000;
        border: 2px solid #000000;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: bold;
    }
    
    QPushButton[objectName="import_btn"]:hover {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* ===== UNIFIED COMPACT INTERFACE STYLES ===== */
    
    QGroupBox[objectName="compact_section"] {
        font-size: 10px;
        font-weight: bold;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 3px;
        margin-top: 5px;
        padding-top: 8px;
        width: 180px;     /* Reduced for more compact panels */
        min-width: 150px; /* Reduced for more compact panels */
        max-width: 300px; /* Increased maximum for flexibility */
    }
    
    QGroupBox[objectName="compact_section"]::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 5px 0 5px;
        font-size: 9px;
    }
    
    QPushButton[objectName="compact_btn"] {
        background-color: #f8f8f8;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 2px;
        padding: 3px 6px;
        font-size: 9px;
        font-weight: normal;
        min-height: 16px;
        max-height: 18px;
        max-width: 140px;
        margin: 1px;
    }
    
    QPushButton[objectName="compact_btn"]:hover {
        background-color: #e8e8e8;
        border-color: #999999;
    }
    
    QPushButton[objectName="compact_btn"]:pressed {
        background-color: #cccccc;
        border-color: #666666;
    }
    
    QPushButton[objectName="settings_wheel"] {
        background-color: #ffffff;
        color: #666666;
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 0px;
        font-size: 7px;
        min-width: 14px;
        max-width: 16px;
        min-height: 14px;
        max-height: 16px;
    }
    
    QPushButton[objectName="settings_wheel"]:hover {
        background-color: #f0f0f0;
        color: #333333;
        border-color: #999999;
    }
    
    QPushButton[objectName="settings_wheel"]:pressed {
        background-color: #e0e0e0;
        color: #000000;
        border-color: #666666;
    }
    
    QLabel[objectName="progress_compact"] {
        font-size: 8px;
        color: #666666;
        padding: 1px;
        margin: 0px;
    }
    
    /* Compact dialog styles */
    QDialog {
        background-color: #ffffff;
        color: #000000;
        border: 2px solid #000000;
    }
    
    QDialog QLabel {
        font-size: 11px;
        color: #333333;
        padding: 2px;
    }
    
    QDialog QDoubleSpinBox, QDialog QSpinBox, QDialog QLineEdit, QDialog QComboBox {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 4px;
        font-size: 11px;
        min-height: 20px;
    }
    
    QDialog QDoubleSpinBox:focus, QDialog QSpinBox:focus, QDialog QLineEdit:focus, QDialog QComboBox:focus {
        border-color: #000000;
    }
    
    QDialogButtonBox QPushButton {
        background-color: #f8f8f8;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 6px 12px;
        font-size: 11px;
        min-width: 60px;
    }
    
    QDialogButtonBox QPushButton:hover {
        background-color: #e8e8e8;
        border-color: #999999;
    }
    
    QDialogButtonBox QPushButton:default {
        background-color: #000000;
        color: #ffffff;
        border-color: #000000;
    }
    
    QDialogButtonBox QPushButton:default:hover {
        background-color: #333333;
    }
    """