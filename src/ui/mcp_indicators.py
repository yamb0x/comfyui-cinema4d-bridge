"""
Enhanced MCP Status Indicators with Dual Functionality
Professional status display with click-to-refresh functionality
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCursor, QPainter, QPen, QColor
from enum import Enum


class ConnectionStatus(Enum):
    """Connection status states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class MCPIndicator(QWidget):
    """
    Enhanced MCP indicator with dual functionality:
    - Visual status display
    - Click-to-refresh functionality
    """
    
    # Signals
    refresh_requested = Signal()
    status_changed = Signal(str)  # status name
    
    def __init__(self, service_name: str, address: str, parent=None):
        super().__init__(parent)
        self.service_name = service_name
        self.address = address
        self.status = ConnectionStatus.DISCONNECTED
        
        # UI components
        self.status_circle = None
        self.service_label = None
        self.address_label = None
        
        # Animation properties
        self.pulse_animation = None
        self.is_pulsing = False
        
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        """Setup the indicator UI"""
        # Make widget clickable
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(f"Click to refresh {self.service_name} connection")
        
        # Main layout - reduced margins to fit in 36px header space
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(1)
        layout.setAlignment(Qt.AlignLeft)
        
        # Main status line (circle + service name)
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        
        # Status circle - ensure it's properly centered and sized
        self.status_circle = QLabel("●")
        self.status_circle.setObjectName("status_circle_disconnected")
        self.status_circle.setFixedSize(16, 16)
        self.status_circle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_circle)
        
        # Service name
        self.service_label = QLabel(self.service_name)
        self.service_label.setObjectName("status_text")
        main_layout.addWidget(self.service_label)
        
        layout.addWidget(main_widget)
        
        # Address info
        self.address_label = QLabel(self.address)
        self.address_label.setObjectName("mcp_address_label")
        layout.addWidget(self.address_label)
        
        # Apply initial styling
        self.update_visual_state()
        
    def setup_animations(self):
        """Setup status animations"""
        # Pulse animation for connecting state
        self.pulse_animation = QPropertyAnimation(self.status_circle, b"color")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
        
    def mousePressEvent(self, event):
        """Handle click to refresh"""
        if event.button() == Qt.LeftButton:
            self.refresh_requested.emit()
            self.set_status(ConnectionStatus.CONNECTING)
        super().mousePressEvent(event)
        
    def set_status(self, status: ConnectionStatus, message: str = None):
        """Update connection status"""
        self.status = status
        
        # Update address if message provided
        if message:
            self.address_label.setText(message)
        
        self.update_visual_state()
        self.status_changed.emit(status.value)
        
    def update_visual_state(self):
        """Update visual state based on status"""
        if self.status == ConnectionStatus.CONNECTED:
            self.status_circle.setObjectName("status_circle_connected")
            self.stop_pulse()
            
        elif self.status == ConnectionStatus.CONNECTING:
            self.status_circle.setObjectName("status_circle_connecting")
            self.start_pulse()
            
        elif self.status == ConnectionStatus.ERROR:
            self.status_circle.setObjectName("status_circle_disconnected")
            self.stop_pulse()
            
        else:  # DISCONNECTED
            self.status_circle.setObjectName("status_circle_disconnected")
            self.stop_pulse()
        
        # Force style refresh
        self.status_circle.style().unpolish(self.status_circle)
        self.status_circle.style().polish(self.status_circle)
        
    def start_pulse(self):
        """Start pulsing animation for connecting state"""
        if not self.is_pulsing:
            self.is_pulsing = True
            # Note: QPropertyAnimation doesn't work well with QLabel text color
            # We'll use a QTimer instead for pulsing effect
            self.pulse_timer = QTimer()
            self.pulse_timer.timeout.connect(self._pulse_effect)
            self.pulse_timer.start(500)  # Pulse every 500ms
            
    def stop_pulse(self):
        """Stop pulsing animation"""
        if self.is_pulsing:
            self.is_pulsing = False
            if hasattr(self, 'pulse_timer'):
                self.pulse_timer.stop()
                
    def _pulse_effect(self):
        """Create pulsing effect by alternating opacity"""
        current_text = self.status_circle.text()
        if current_text == "●":
            self.status_circle.setText("○")  # Hollow circle
        else:
            self.status_circle.setText("●")  # Filled circle
            
    def set_service_name(self, name: str):
        """Update service name"""
        self.service_name = name
        self.service_label.setText(name)
        self.setToolTip(f"Click to refresh {name} connection")
        
    def set_address(self, address: str):
        """Update address"""
        self.address = address
        self.address_label.setText(address)


class MCPStatusBar(QWidget):
    """
    Container for MCP status indicators
    """
    
    # Signals
    comfyui_refresh_requested = Signal()
    cinema4d_refresh_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup status bar UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # ComfyUI indicator
        self.comfyui_indicator = MCPIndicator("ComfyUI", "localhost:8188")
        self.comfyui_indicator.refresh_requested.connect(self.comfyui_refresh_requested.emit)
        layout.addWidget(self.comfyui_indicator)
        
        # Cinema4D indicator
        self.cinema4d_indicator = MCPIndicator("Cinema4D", "localhost:54321")
        self.cinema4d_indicator.refresh_requested.connect(self.cinema4d_refresh_requested.emit)
        layout.addWidget(self.cinema4d_indicator)
        
        layout.addStretch()
        
    def set_comfyui_status(self, status: ConnectionStatus, message: str = None):
        """Update ComfyUI status"""
        self.comfyui_indicator.set_status(status, message)
        
    def set_cinema4d_status(self, status: ConnectionStatus, message: str = None):
        """Update Cinema4D status"""
        self.cinema4d_indicator.set_status(status, message)
        
    def get_comfyui_status(self) -> ConnectionStatus:
        """Get ComfyUI status"""
        return self.comfyui_indicator.status
        
    def get_cinema4d_status(self) -> ConnectionStatus:
        """Get Cinema4D status"""
        return self.cinema4d_indicator.status