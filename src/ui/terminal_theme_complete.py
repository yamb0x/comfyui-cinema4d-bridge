"""
Complete Terminal Theme for comfy2c4d
Professional monospace aesthetic with comprehensive UI coverage
"""

def get_complete_terminal_theme() -> str:
    """
    Complete terminal theme with all UI elements, MCP indicators, dynamic panels,
    console color coding, and professional monospace aesthetic
    """
    return """
    /* ==== JETBRAINS MONO FONT IMPORT ==== */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
    
    /* ==== ROOT APPLICATION STYLES ==== */
    QMainWindow {
        background-color: #000000;
        color: #fafafa;
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 12px;
        font-weight: 400;
        line-height: 1.3;
    }
    
    QWidget {
        background-color: #000000;
        color: #fafafa;
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
        border: none;
        margin: 0px;
        padding: 0px;
    }
    
    /* ==== MAIN HEADER STYLES ==== */
    QWidget#main_header {
        background-color: #0a0a0a;
        border-bottom: 1px solid #262626;
        min-height: 60px;
        max-height: 60px;
        padding: 0px 20px;
    }
    
    /* ==== MCP STATUS INDICATORS WITH DUAL FUNCTIONALITY ==== */
    /* ComfyUI Status Container */
    QWidget#comfyui_container {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 0px 4px;
    }
    
    QWidget#comfyui_container:hover {
        background-color: #171717;
        border-color: #404040;
    }
    
    /* Cinema4D Status Container */
    QWidget#c4d_container {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 0px 4px;
    }
    
    QWidget#c4d_container:hover {
        background-color: #171717;
        border-color: #404040;
    }
    
    /* ==== MESSAGE BOX STYLING ==== */
    QMessageBox {
        background-color: #2b2b2b;
        color: #fafafa;
    }
    
    QMessageBox QLabel {
        background-color: transparent !important;
        color: #fafafa;
        padding: 0px;
    }
    
    QMessageBox QPushButton {
        background-color: #404040;
        border: 1px solid #525252;
        color: #fafafa;
        padding: 6px 16px;
        border-radius: 3px;
        min-width: 60px;
    }
    
    QMessageBox QPushButton:hover {
        background-color: #525252;
        border: 1px solid #626262;
    }
    
    QMessageBox QPushButton:pressed {
        background-color: #333333;
    }
    
    /* Status Circle Colors */
    QLabel#status_circle_connected {
        color: #4CAF50;
        font-size: 14px;
        font-weight: bold;
        margin: 0px 2px;
    }
    
    QLabel#status_circle_disconnected {
        color: #ef4444;
        font-size: 14px;
        font-weight: bold;
        margin: 0px 2px;
    }
    
    QLabel#status_circle_connecting {
        color: #eab308;
        font-size: 14px;
        font-weight: bold;
        margin: 0px 2px;
    }
    
    /* Status Text */
    QLabel#status_text {
        background-color: transparent;
        color: #fafafa;
        font-size: 11px;
        font-weight: 500;
        margin: 0px;
        padding: 0px;
    }
    
    QLabel#connection_info {
        background-color: transparent;
        color: #737373;
        font-size: 9px;
        font-weight: 400;
        margin: 0px;
        padding: 0px;
    }
    
    QLabel#performance_meter_label {
        background-color: transparent;
        color: #737373;
        font-size: 9px;
        font-weight: 400;
        margin: 0px;
        padding: 0px;
    }
    
    QLabel#mcp_address_label {
        background-color: transparent;
        color: #737373;
        font-size: 9px;
        font-weight: 400;
        margin: 0px;
        padding: 0px;
    }
    
    QLabel#object_count_label {
        background-color: transparent;
        color: #737373;
        font-size: 9px;
        font-weight: 400;
        margin: 0px;
        padding: 0px;
    }
    
    /* ==== TAB SYSTEM STYLES ==== */
    QTabWidget::pane {
        background-color: #000000;
        border: none;
        border-top: 1px solid #262626;
    }
    
    QTabWidget::tab-bar {
        alignment: left;
        background-color: #0a0a0a;
    }
    
    QTabBar {
        background-color: #0a0a0a;
        border-bottom: 1px solid #262626;
        qproperty-drawBase: 0;
    }
    
    QTabBar::tab {
        background-color: transparent;
        color: #737373;
        font-size: 11px;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 24px;
        margin-right: 0px;
        border: none;
        border-bottom: 2px solid transparent;
        min-width: 120px;
    }
    
    QTabBar::tab:selected {
        color: #fafafa;
        border-bottom: 2px solid #4CAF50;
        background-color: rgba(34, 197, 94, 0.05);
    }
    
    QTabBar::tab:hover:!selected {
        color: #a3a3a3;
        background-color: rgba(250, 250, 250, 0.02);
        border-bottom: 2px solid #525252;
    }
    
    /* ==== DYNAMIC PANELS SYSTEM ==== */
    /* Left Panel */
    QWidget#left_panel {
        background-color: #0a0a0a;
        border-right: 1px solid #262626;
        min-width: 250px;
        max-width: 1200px;
    }
    
    /* Right Panel */
    QWidget#right_panel {
        background-color: #0a0a0a;
        border-left: 1px solid #262626;
        min-width: 250px;
        max-width: 1200px;
    }
    
    /* Center Content Area */
    QWidget#content_area {
        background-color: #000000;
    }
    
    /* ==== SECTION STYLES ==== */
    QWidget#sidebar_section {
        background-color: transparent;
        border-bottom: 1px solid #262626;
        padding: 16px;
    }
    
    QLabel#section_title {
        background-color: transparent;
        color: #737373;
        font-size: 10px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 0px 0px 4px 0px;
        padding: 0px;
    }
    
    /* ==== FORM CONTROLS ==== */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #171717;
        border: 1px solid #404040;
        border-radius: 3px;
        color: #fafafa;
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 11px;
        padding: 8px 12px;
        selection-background-color: #3b82f6;
        selection-color: #fafafa;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border-color: #4CAF50;
        outline: none;
        box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.3);
    }
    
    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {
        border-color: #525252;
    }
    
    /* Magic Prompt Button */
    QPushButton#magic_btn {
        background-color: rgba(34, 197, 94, 0.1);
        border: 1px solid #4CAF50;
        border-radius: 3px;
        color: #4CAF50;
        font-size: 10px;
        font-weight: 500;
        padding: 4px 8px;
        margin: 2px;
        min-width: 20px;
        max-width: 30px;
    }
    
    QPushButton#magic_btn:hover {
        background-color: rgba(34, 197, 94, 0.2);
        border-color: #16a34a;
        color: #16a34a;
    }
    
    QPushButton#magic_btn:pressed {
        background-color: rgba(34, 197, 94, 0.3);
        border-color: #15803d;
        color: #15803d;
    }
    
    /* ==== COMBO BOXES ==== */
    QComboBox {
        background-color: #171717;
        border: 1px solid #404040;
        border-radius: 3px;
        color: #fafafa;
        font-size: 11px;
        padding: 6px 8px;
        min-height: 20px;
    }
    
    QComboBox:focus {
        border-color: #4CAF50;
    }
    
    QComboBox:hover {
        border-color: #525252;
    }
    
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #404040;
        background-color: #262626;
        border-radius: 0px 3px 3px 0px;
    }
    
    QComboBox::down-arrow {
        image: none;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #fafafa;
    }
    
    QComboBox QAbstractItemView {
        background-color: #171717;
        border: 1px solid #404040;
        selection-background-color: #262626;
        color: #fafafa;
        outline: none;
    }
    
    QComboBox QAbstractItemView::item {
        padding: 6px 8px;
        border: none;
        min-height: 20px;
    }
    
    QComboBox QAbstractItemView::item:selected {
        background-color: #4CAF50;
        color: #000000;
    }
    
    /* ==== SPIN BOXES ==== */
    QSpinBox, QDoubleSpinBox {
        background-color: #171717;
        border: 1px solid #404040;
        border-radius: 3px;
        color: #fafafa;
        font-size: 11px;
        padding: 6px 8px;
        min-height: 20px;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #4CAF50;
    }
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 16px;
        background-color: #262626;
        border-left: 1px solid #404040;
        border-radius: 0px 3px 0px 0px;
    }
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 16px;
        background-color: #262626;
        border-left: 1px solid #404040;
        border-radius: 0px 0px 3px 0px;
    }
    
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        image: none;
        width: 0;
        height: 0;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-bottom: 4px solid #fafafa;
    }
    
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        image: none;
        width: 0;
        height: 0;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-top: 4px solid #fafafa;
    }
    
    /* ==== BUTTONS ==== */
    QPushButton {
        background-color: #262626;
        border: 1px solid #404040;
        border-radius: 3px;
        color: #fafafa;
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 11px;
        font-weight: 500;
        padding: 8px 16px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        min-height: 16px;
    }
    
    QPushButton:hover {
        background-color: #404040;
        border-color: #525252;
    }
    
    QPushButton:pressed {
        background-color: #171717;
        border-color: #262626;
    }
    
    QPushButton:disabled {
        background-color: #171717;
        color: #525252;
        border-color: #262626;
    }
    
    /* Primary Buttons */
    QPushButton#generate_btn, QPushButton#primary_btn, QPushButton#generate_image_btn, 
    QPushButton#generate_3d_btn, QPushButton#generate_texture_btn {
        background-color: #4CAF50;
        color: #000000;
        border-color: #4CAF50;
        font-weight: 600;
    }
    
    QPushButton#generate_btn:hover, QPushButton#primary_btn:hover, QPushButton#generate_image_btn:hover,
    QPushButton#generate_3d_btn:hover, QPushButton#generate_texture_btn:hover {
        background-color: #16a34a;
        border-color: #16a34a;
    }
    
    QPushButton#generate_btn:pressed, QPushButton#primary_btn:pressed, QPushButton#generate_image_btn:pressed,
    QPushButton#generate_3d_btn:pressed, QPushButton#generate_texture_btn:pressed {
        background-color: #15803d;
        border-color: #15803d;
    }
    
    /* Secondary Buttons */
    QPushButton#secondary_btn, QPushButton#refresh_btn, QPushButton#clear_btn {
        background-color: transparent;
        border: 1px solid #404040;
        color: #a3a3a3;
        padding: 6px 12px;
    }
    
    QPushButton#secondary_btn:hover, QPushButton#refresh_btn:hover, QPushButton#clear_btn:hover {
        background-color: #262626;
        color: #fafafa;
        border-color: #525252;
    }
    
    /* ==== CHECKBOXES ==== */
    QCheckBox {
        color: #fafafa;
        font-size: 11px;
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        background-color: #171717;
        border: 1px solid #404040;
        border-radius: 3px;
    }
    
    QCheckBox::indicator:checked {
        background-color: #4CAF50;
        border-color: #4CAF50;
    }
    
    QCheckBox::indicator:checked::after {
        content: "";
        width: 6px;
        height: 3px;
        border: 2px solid #000000;
        border-top: none;
        border-right: none;
    }
    
    /* ==== IMAGE GRID WIDGETS ==== */
    QWidget#image_grid_item {
        background-color: #171717;
        border: 1px solid #262626;
        border-radius: 3px;
        min-height: 180px;
        min-width: 180px;
    }
    
    QWidget#image_grid_item:hover {
        border-color: #404040;
    }
    
    QWidget#image_grid_item[selected="true"] {
        border-color: #4CAF50;
        border-width: 2px;
    }
    
    QLabel#image_placeholder {
        background-color: transparent;
        color: #525252;
        font-size: 10px;
        text-align: center;
        margin: 0px;
        padding: 20px;
    }
    
    /* ==== 3D MODEL GRID WIDGETS ==== */
    QWidget#model_grid_item {
        background-color: #171717;
        border: 1px solid #262626;
        border-radius: 3px;
        min-height: 200px;
        min-width: 200px;
    }
    
    QWidget#model_grid_item:hover {
        border-color: #404040;
    }
    
    QWidget#model_grid_item[selected="true"] {
        border-color: #3b82f6;
        border-width: 2px;
    }
    
    /* ==== CONSOLE SYSTEM WITH COLOR CODING ==== */
    QWidget#console_container {
        background-color: #0a0a0a;
        border-top: 1px solid #262626;
        min-height: 120px;
        max-height: 200px;
    }
    
    QTextEdit#console {
        background-color: #0a0a0a;
        border: none;
        color: #737373;
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 10px;
        line-height: 1.0;
        padding: 8px 16px;
    }
    
    /* Console Text Colors for Different Log Levels */
    .console-timestamp {
        color: #525252;
        font-weight: 400;
    }
    
    .console-debug {
        color: #737373;
        font-weight: 400;
    }
    
    .console-info {
        color: #3b82f6;
        font-weight: 500;
    }
    
    .console-success {
        color: #4CAF50;
        font-weight: 500;
    }
    
    .console-warning {
        color: #eab308;
        font-weight: 500;
    }
    
    .console-error {
        color: #ef4444;
        font-weight: 600;
    }
    
    .console-critical {
        color: #dc2626;
        font-weight: 700;
    }
    
    /* ==== SCROLL AREAS ==== */
    QScrollArea {
        background-color: #000000;
        border: none;
    }
    
    QScrollArea > QWidget > QWidget {
        background-color: #000000;
    }
    
    /* ==== SCROLLBARS ==== */
    QScrollBar:vertical {
        background-color: #0a0a0a;
        width: 6px;
        border: none;
        border-radius: 3px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #404040;
        border-radius: 3px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #525252;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
        height: 0px;
    }
    
    QScrollBar:horizontal {
        background-color: #0a0a0a;
        height: 6px;
        border: none;
        border-radius: 3px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #404040;
        border-radius: 3px;
        min-width: 20px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #525252;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        border: none;
        background: none;
        width: 0px;
    }
    
    /* ==== SPLITTERS ==== */
    QSplitter::handle {
        background-color: #262626;
    }
    
    QSplitter::handle:horizontal {
        width: 1px;
        background-image: repeating-linear-gradient(
            to bottom,
            #404040 0px,
            #404040 2px,
            transparent 2px,
            transparent 4px
        );
    }
    
    QSplitter::handle:vertical {
        height: 1px;
        background-image: repeating-linear-gradient(
            to right,
            #404040 0px,
            #404040 2px,
            transparent 2px,
            transparent 4px
        );
    }
    
    QSplitter::handle:horizontal:hover {
        background-image: repeating-linear-gradient(
            to bottom,
            #525252 0px,
            #525252 3px,
            transparent 3px,
            transparent 6px
        );
    }
    
    QSplitter::handle:vertical:hover {
        background-image: repeating-linear-gradient(
            to right,
            #525252 0px,
            #525252 3px,
            transparent 3px,
            transparent 6px
        );
    }
    
    /* ==== LIST WIDGETS ==== */
    QListWidget {
        background-color: #171717;
        border: 1px solid #262626;
        border-radius: 3px;
        alternate-background-color: #1a1a1a;
        outline: none;
    }
    
    QListWidget::item {
        background-color: transparent;
        color: #fafafa;
        padding: 8px 12px;
        border-bottom: 1px solid #262626;
        min-height: 16px;
    }
    
    QListWidget::item:selected {
        background-color: #4CAF50;
        color: #000000;
    }
    
    QListWidget::item:hover {
        background-color: #262626;
    }
    
    /* ==== GROUP BOXES ==== */
    QGroupBox {
        background-color: transparent;
        border: 1px solid #262626;
        border-radius: 3px;
        color: #737373;
        font-size: 10px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 12px;
        padding-top: 16px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0px 8px;
        background-color: #000000;
        color: #737373;
    }
    
    /* ==== MENU BAR ==== */
    QMenuBar {
        background-color: #000000;
        color: #fafafa;
        border-bottom: 1px solid #262626;
        font-size: 11px;
        padding: 2px;
    }
    
    QMenuBar::item {
        background-color: transparent;
        color: #fafafa;
        padding: 6px 12px;
        border-radius: 3px;
    }
    
    QMenuBar::item:selected {
        background-color: #262626;
    }
    
    QMenuBar::item:pressed {
        background-color: #404040;
    }
    
    /* ==== MENUS ==== */
    QMenu {
        background-color: #171717;
        border: 1px solid #404040;
        border-radius: 3px;
        color: #fafafa;
        font-size: 11px;
        padding: 4px;
    }
    
    QMenu::item {
        background-color: transparent;
        color: #fafafa;
        padding: 6px 16px;
        border-radius: 3px;
    }
    
    QMenu::item:selected {
        background-color: #262626;
    }
    
    QMenu::item:disabled {
        color: #525252;
    }
    
    QMenu::separator {
        background-color: #404040;
        height: 1px;
        margin: 4px 8px;
    }
    
    /* ==== DIALOG BOXES ==== */
    QDialog {
        background-color: #171717;
        color: #fafafa;
        border: 1px solid #404040;
        border-radius: 3px;
    }
    
    QDialogButtonBox QPushButton {
        min-width: 80px;
        padding: 6px 16px;
    }
    
    /* ==== TOOL TIPS ==== */
    QToolTip {
        background-color: #262626;
        color: #fafafa;
        border: 1px solid #404040;
        border-radius: 3px;
        font-size: 10px;
        padding: 6px 8px;
    }
    
    /* ==== PROGRESS BARS ==== */
    QProgressBar {
        background-color: #171717;
        border: 1px solid #404040;
        border-radius: 3px;
        color: #fafafa;
        font-size: 10px;
        text-align: center;
        padding: 2px;
    }
    
    QProgressBar::chunk {
        background-color: #4CAF50;
        border-radius: 2px;
    }
    
    /* ==== CINEMA4D CHAT INTERFACE ==== */
    QWidget#chat_container {
        background-color: #0a0a0a;
        border: 1px solid #262626;
        border-radius: 3px;
    }
    
    QTextEdit#chat_display {
        background-color: #0a0a0a;
        border: none;
        color: #fafafa;
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 11px;
        padding: 12px;
    }
    
    QLineEdit#chat_input {
        background-color: #171717;
        border: 1px solid #404040;
        border-radius: 3px;
        color: #fafafa;
        font-size: 11px;
        padding: 8px 12px;
        margin: 8px;
    }
    
    QLineEdit#chat_input:focus {
        border-color: #4CAF50;
    }
    
    /* ==== TEXTURE VIEWER INTEGRATION ==== */
    QWidget#texture_viewer_container {
        background-color: #000000;
        border: 1px solid #262626;
        border-radius: 3px;
        min-height: 400px;
    }
    
    QPushButton#launch_texture_viewer {
        background-color: #3b82f6;
        color: #fafafa;
        border-color: #3b82f6;
        font-weight: 600;
    }
    
    QPushButton#launch_texture_viewer:hover {
        background-color: #2563eb;
        border-color: #2563eb;
    }
    
    /* ==== SPECIAL STATES ==== */
    QWidget:disabled {
        opacity: 0.6;
    }
    
    QWidget:focus {
        outline: none;
    }
    
    /* ==== RESPONSIVE ADJUSTMENTS ==== */
    QWidget[size="compact"] {
        padding: 8px;
    }
    
    QWidget[size="compact"] QLabel#section_title {
        font-size: 9px;
        margin-bottom: 8px;
    }
    
    QWidget[size="compact"] QPushButton {
        padding: 6px 12px;
        font-size: 10px;
    }
    """


def get_console_color_map() -> dict:
    """
    Get color mapping for console log levels with HTML formatting
    """
    return {
        'timestamp': '#525252',
        'debug': '#737373',
        'info': '#3b82f6',
        'success': '#4CAF50',
        'warning': '#eab308',
        'error': '#ef4444',
        'critical': '#dc2626',
        'message': '#a3a3a3'
    }


def format_console_message(level: str, message: str, timestamp: str = None) -> str:
    """
    Format console message with proper color coding
    """
    color_map = get_console_color_map()
    
    if timestamp is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S]")
    
    timestamp_color = color_map['timestamp']
    level_color = color_map.get(level.lower(), color_map['info'])
    message_color = color_map['message']
    
    return f'''
    <div style="margin-bottom: 2px; font-family: 'JetBrains Mono', monospace;">
        <span style="color: {timestamp_color}; font-weight: 400;">{timestamp}</span>
        <span style="color: {level_color}; font-weight: 500; margin: 0 8px;">{level.upper()}</span>
        <span style="color: {message_color}; font-weight: 400;">{message}</span>
    </div>
    '''