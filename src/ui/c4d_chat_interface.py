"""
Cinema4D Intelligent Chat Interface
Natural language interface for Cinema4D scene creation
"""

from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QSplitter, QLineEdit,
    QFileDialog, QToolButton, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer, Slot, QEvent
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont

from utils.logger import LoggerMixin


class ChatHistoryWidget(QTextEdit):
    """Custom chat history display with rich formatting"""
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setObjectName("chat_history")
        self.document().setDocumentMargin(10)
        
    def add_message(self, text: str, sender: str = "user", images: List[str] = None):
        """Add a formatted message to chat history"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor("#888888"))
        timestamp_format.setFontPointSize(10)
        cursor.insertText(f"[{timestamp}] ", timestamp_format)
        
        # Add sender
        sender_format = QTextCharFormat()
        if sender == "user":
            sender_format.setForeground(QColor("#0084ff"))
            sender_format.setFontWeight(QFont.Weight.Bold)
            cursor.insertText("You: ", sender_format)
        else:
            sender_format.setForeground(QColor("#00c853"))
            sender_format.setFontWeight(QFont.Weight.Bold)
            cursor.insertText("AI: ", sender_format)
        
        # Add message text
        message_format = QTextCharFormat()
        message_format.setForeground(QColor("#e0e0e0"))
        cursor.insertText(text + "\n", message_format)
        
        # Add images if provided
        if images:
            for img_path in images:
                cursor.insertText(f"  📎 {img_path}\n", message_format)
        
        cursor.insertText("\n")
        
        # Scroll to bottom
        self.setTextCursor(cursor)
        self.ensureCursorVisible()


class ChatInputArea(QWidget):
    """Input area with text field and control buttons"""
    
    message_sent = Signal(str, list)  # text, images
    
    def __init__(self):
        super().__init__()
        self.attached_images = []
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add image button
        self.add_image_btn = QToolButton()
        self.add_image_btn.setText("📎")
        self.add_image_btn.setObjectName("attach_btn")
        self.add_image_btn.setToolTip("Attach reference images")
        self.add_image_btn.clicked.connect(self.attach_images)
        layout.addWidget(self.add_image_btn)
        
        # Text input
        self.text_input = QTextEdit()
        self.text_input.setObjectName("chat_input")
        self.text_input.setMaximumHeight(100)
        self.text_input.setPlaceholderText("Describe what you want to create...")
        layout.addWidget(self.text_input)
        
        # Send button
        self.send_btn = QPushButton("→")
        self.send_btn.setObjectName("send_btn")
        self.send_btn.setToolTip("Send message (Enter)")
        self.send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.send_btn)
        
        self.setLayout(layout)
        
        # Connect Enter key
        self.text_input.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """Handle Enter key in text input"""
        if obj == self.text_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers():
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def attach_images(self):
        """Open file dialog to attach images"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Reference Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if files:
            self.attached_images.extend(files)
            self.update_attachment_indicator()
    
    def update_attachment_indicator(self):
        """Update UI to show attached files"""
        if self.attached_images:
            self.add_image_btn.setText(f"📎 ({len(self.attached_images)})")
            self.add_image_btn.setToolTip(f"Attached: {', '.join(self.attached_images)}")
        else:
            self.add_image_btn.setText("📎")
            self.add_image_btn.setToolTip("Attach reference images")
    
    def send_message(self):
        """Send the message"""
        text = self.text_input.toPlainText().strip()
        if text:
            self.message_sent.emit(text, self.attached_images.copy())
            self.text_input.clear()
            self.attached_images.clear()
            self.update_attachment_indicator()


class C4DIntelligentChat(QWidget, LoggerMixin):
    """Main chat interface for Cinema4D scene intelligence"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the chat interface UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.header = QLabel("🎬 Cinema4D Scene Intelligence")
        self.header.setObjectName("chat_header")
        header_layout.addWidget(self.header)
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("chat_status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)
        
        # Chat history
        self.chat_history = ChatHistoryWidget()
        layout.addWidget(self.chat_history, 1)
        
        # Input area
        self.input_area = ChatInputArea()
        layout.addWidget(self.input_area)
        
        self.setLayout(layout)
        
        # Add welcome message
        QTimer.singleShot(100, self.show_welcome_message)
        
    def setup_connections(self):
        """Connect signals and slots"""
        self.input_area.message_sent.connect(self.on_message_sent)
        
    def show_welcome_message(self):
        """Display welcome message in chat"""
        welcome_text = (
            "Welcome! I can help you create Cinema4D scenes using natural language. "
            "Try commands like:\n"
            "• 'Create a landscape with scattered trees'\n"
            "• 'Make an abstract composition with organic shapes'\n"
            "• 'Generate a grid of cubes with random colors'\n"
            "• 'Connect these objects with dynamic splines'"
        )
        self.chat_history.add_message(welcome_text, "assistant")
        
    @Slot(str, list)
    def on_message_sent(self, message: str, images: List[str]):
        """Handle user message"""
        # Add to chat history
        self.chat_history.add_message(message, "user", images)
        
        # Update status
        self.set_status("Processing...")
        
        # Process message asynchronously
        if self.parent_app:
            QTimer.singleShot(100, lambda: self.process_message_async(message, images))
        else:
            # For testing without full app
            self.chat_history.add_message(
                "Test mode: Message received. Full processing requires app integration.",
                "assistant"
            )
            self.set_status("Ready")
    
    def process_message_async(self, message: str, images: List[str]):
        """Process message through the intelligence pipeline"""
        try:
            # This will be connected to the NLP parser and execution engine
            self.parent_app._run_async_task(self._process_message(message, images))
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.chat_history.add_message(
                f"Error: {str(e)}. Please check the logs for details.",
                "assistant"
            )
            self.set_status("Error")
    
    async def _process_message(self, message: str, images: List[str]):
        """Async message processing"""
        try:
            # Update UI to show processing
            QTimer.singleShot(0, lambda: self.chat_history.add_message(
                "🤔 Understanding your request...", "assistant"
            ))
            
            # Parse natural language
            if hasattr(self.parent_app, 'nlp_parser') and hasattr(self.parent_app, 'operation_generator'):
                intent = await self.parent_app.nlp_parser.parse(message)
                
                self.logger.info(f"Parsed intent: {intent}")
                
                # Show confidence
                if intent.confidence < 0.5:
                    QTimer.singleShot(0, lambda: self.chat_history.add_message(
                        "⚠️ I'm not entirely sure I understood. Let me try...", "assistant"
                    ))
                
                # Generate operations
                operations = await self.parent_app.operation_generator.generate(intent)
                
                if not operations:
                    QTimer.singleShot(0, lambda: self.chat_history.add_message(
                        "❓ I couldn't understand that command. Try something like:\n"
                        "• 'Create a sphere'\n"
                        "• 'Make 10 cubes in a grid'\n"
                        "• 'Scatter objects randomly'",
                        "assistant"
                    ))
                    self.set_status("Ready")
                    return
                
                # Execute operations
                for op in operations:
                    self.logger.info(f"Executing operation: {op.description}")
                    self.logger.debug(f"Operation params: {op.parameters}")
                    
                    QTimer.singleShot(0, lambda desc=op.description: 
                        self.chat_history.add_message(f"🔄 {desc}", "assistant")
                    )
                    
                    result = await self.parent_app.operation_executor.execute(op)
                    
                    self.logger.info(f"Operation result: success={result.success}, message={result.message}, error={result.error}")
                    
                    if result.success:
                        QTimer.singleShot(0, lambda msg=result.message: 
                            self.chat_history.add_message(f"✅ {msg}", "assistant")
                        )
                    else:
                        QTimer.singleShot(0, lambda err=result.error: 
                            self.chat_history.add_message(f"❌ {err}", "assistant")
                        )
                
                # Final success message
                QTimer.singleShot(0, lambda: self.chat_history.add_message(
                    "🎉 Done! Check Cinema4D to see your creation.", "assistant"
                ))
                
            else:
                # Fallback for initial implementation or test mode
                self.logger.warning("Intelligence systems not fully initialized")
                
                # Simple keyword-based execution
                message_lower = message.lower()
                
                if "cube" in message_lower:
                    result = await self.parent_app.mcp_wrapper.add_primitive("cube", size=200)
                    if result.success:
                        QTimer.singleShot(0, lambda: self.chat_history.add_message(
                            "✅ Created a cube in Cinema4D", "assistant"
                        ))
                    else:
                        QTimer.singleShot(0, lambda: self.chat_history.add_message(
                            f"❌ Failed to create cube: {result.error}", "assistant"
                        ))
                
                elif "sphere" in message_lower:
                    result = await self.parent_app.mcp_wrapper.add_primitive("sphere", size=150)
                    if result.success:
                        QTimer.singleShot(0, lambda: self.chat_history.add_message(
                            "✅ Created a sphere in Cinema4D", "assistant"
                        ))
                    else:
                        QTimer.singleShot(0, lambda: self.chat_history.add_message(
                            f"❌ Failed to create sphere: {result.error}", "assistant"
                        ))
                
                elif "test" in message_lower:
                    await self.parent_app._test_cinema4d_cube()
                    QTimer.singleShot(0, lambda: self.chat_history.add_message(
                        "✅ Created test cube in Cinema4D", "assistant"
                    ))
                
                else:
                    QTimer.singleShot(0, lambda: self.chat_history.add_message(
                        "I can understand basic commands like:\n"
                        "• 'Create a cube'\n"
                        "• 'Create a sphere'\n"
                        "• 'Test connection'\n\n"
                        "Full natural language processing is initializing...",
                        "assistant"
                    ))
            
            self.set_status("Ready")
            
        except Exception as e:
            self.logger.error(f"Error in message processing: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            QTimer.singleShot(0, lambda: self.chat_history.add_message(
                f"😔 Sorry, I encountered an error: {str(e)}\n"
                "Please check the logs for details.",
                "assistant"
            ))
            self.set_status("Error")
    
    def set_status(self, status: str):
        """Update status label"""
        # Ensure UI update happens on main thread
        QTimer.singleShot(0, lambda: self.status_label.setText(status))
        
        # Color based on status
        if status == "Ready":
            self.status_label.setStyleSheet("color: #00c853;")
        elif status == "Processing...":
            self.status_label.setStyleSheet("color: #ffab00;")
        elif status == "Error":
            self.status_label.setStyleSheet("color: #ff5252;")