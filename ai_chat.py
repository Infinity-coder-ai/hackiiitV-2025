"""AI Chat Widget for interacting with the Gemini-powered AI assistant."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QScrollArea, QSizePolicy, 
                             QMenu, QMenuBar, QMainWindow, QToolBar, QDialog,
                             QSlider, QCheckBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QAction, QIcon, QPixmap, QGuiApplication, QColor
import json
import os
from datetime import datetime
from simple_chat import SimpleChat

class SettingsDialog(QDialog):
    """Dialog for chatbot settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chatbot Settings")
        self.resize(400, 300)
        
        # Load settings or use defaults
        self.settings = self.load_settings()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI for settings dialog."""
        layout = QVBoxLayout(self)
        
        # Temperature setting
        temp_layout = QHBoxLayout()
        temp_label = QLabel("Temperature:")
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(100)
        self.temp_slider.setValue(int(self.settings.get("temperature", 0.7) * 100))
        self.temp_value = QLabel(f"{self.settings.get('temperature', 0.7):.1f}")
        
        self.temp_slider.valueChanged.connect(self.update_temp_value)
        
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_value)
        
        # Dark mode toggle
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Dark Theme:")
        self.theme_checkbox = QCheckBox()
        self.theme_checkbox.setChecked(self.settings.get("dark_theme", True))
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_checkbox)
        theme_layout.addStretch()
        
        # Auto-save history
        save_layout = QHBoxLayout()
        save_label = QLabel("Auto-save Chat History:")
        self.save_checkbox = QCheckBox()
        self.save_checkbox.setChecked(self.settings.get("auto_save", True))
        
        save_layout.addWidget(save_label)
        save_layout.addWidget(self.save_checkbox)
        save_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        save_button.clicked.connect(self.save_settings)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Add all layouts
        layout.addLayout(temp_layout)
        layout.addLayout(theme_layout)
        layout.addLayout(save_layout)
        layout.addStretch()
        layout.addLayout(button_layout)
        
    def update_temp_value(self, value):
        """Update temperature value label when slider changes."""
        temp = value / 100.0
        self.temp_value.setText(f"{temp:.1f}")
        
    def save_settings(self):
        """Save settings and close dialog."""
        settings = {
            "temperature": self.temp_slider.value() / 100.0,
            "dark_theme": self.theme_checkbox.isChecked(),
            "auto_save": self.save_checkbox.isChecked(),
        }
        
        # Save to file
        settings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings")
        os.makedirs(settings_dir, exist_ok=True)
        
        with open(os.path.join(settings_dir, "chatbot_settings.json"), "w") as f:
            json.dump(settings, f)
            
        self.settings = settings
        self.accept()
        
    def load_settings(self):
        """Load settings from file or return defaults."""
        settings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "settings", 
            "chatbot_settings.json"
        )
        
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
                
        # Default settings
        return {
            "temperature": 0.7,
            "dark_theme": True,
            "auto_save": True,
        }
        
    def get_settings(self):
        """Return the current settings."""
        return self.settings

class ChatMainWindow(QMainWindow):
    """Main window for the Gemini AI Assistant."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemini AI Assistant")
        self.resize(800, 600)
        
        # Initialize settings
        self.settings_dialog = SettingsDialog(self)
        self.settings = self.settings_dialog.get_settings()
        
        # Initialize the chat widget
        self.chat_widget = AIChatWidget(self)
        self.setCentralWidget(self.chat_widget)
        
        # Create menu and toolbar
        self.create_menu()
        self.create_toolbar()
        
        # Apply theme
        self.apply_theme()
        
        # Auto load chat history if enabled
        if self.settings.get("auto_save", True):
            self.chat_widget.load_chat_history()
        
    def create_menu(self):
        """Create the menu bar."""
        # Main menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # New chat action
        new_chat_action = QAction("New Chat", self)
        new_chat_action.setShortcut("Ctrl+N")
        new_chat_action.triggered.connect(self.chat_widget.clear_chat)
        file_menu.addAction(new_chat_action)
        
        # Save chat action
        save_chat_action = QAction("Save Chat", self)
        save_chat_action.setShortcut("Ctrl+S")
        save_chat_action.triggered.connect(self.chat_widget.save_chat_history)
        file_menu.addAction(save_chat_action)
        
        # Load chat action
        load_chat_action = QAction("Load Chat", self)
        load_chat_action.setShortcut("Ctrl+O")
        load_chat_action.triggered.connect(self.chat_widget.load_chat_history)
        file_menu.addAction(load_chat_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        # Copy action
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.chat_widget.copy_selection)
        edit_menu.addAction(copy_action)
        
        # Clear chat action
        clear_action = QAction("Clear Chat", self)
        clear_action.triggered.connect(self.chat_widget.clear_chat)
        edit_menu.addAction(clear_action)
        
        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        
        # Preferences action
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_settings)
        settings_menu.addAction(preferences_action)
        
        # Theme toggle action
        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(theme_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # New chat action
        new_chat_action = QAction("New Chat", self)
        new_chat_action.triggered.connect(self.chat_widget.clear_chat)
        toolbar.addAction(new_chat_action)
        
        # Save chat action
        save_chat_action = QAction("Save Chat", self)
        save_chat_action.triggered.connect(self.chat_widget.save_chat_history)
        toolbar.addAction(save_chat_action)
        
        toolbar.addSeparator()
        
        # Clear chat action
        clear_action = QAction("Clear Chat", self)
        clear_action.triggered.connect(self.chat_widget.clear_chat)
        toolbar.addAction(clear_action)
        
        toolbar.addSeparator()
        
        # Theme toggle action
        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)
        
    def show_settings(self):
        """Show the settings dialog."""
        if self.settings_dialog.exec() == QDialog.DialogCode.Accepted:
            # Update settings
            self.settings = self.settings_dialog.get_settings()
            
            # Apply new settings
            self.apply_theme()
            self.chat_widget.update_settings(self.settings)
            
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        self.settings["dark_theme"] = not self.settings.get("dark_theme", True)
        self.apply_theme()
        
    def apply_theme(self):
        """Apply the current theme based on settings."""
        if self.settings.get("dark_theme", True):
            # Dark theme
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #2c2c2c;
                    color: #f0f0f0;
                }
                QMenuBar {
                    background-color: #2c2c2c;
                    color: #f0f0f0;
                }
                QMenuBar::item:selected {
                    background-color: #3c3c3c;
                }
                QMenu {
                    background-color: #2c2c2c;
                    color: #f0f0f0;
                    border: 1px solid #3c3c3c;
                }
                QMenu::item:selected {
                    background-color: #3c3c3c;
                }
                QToolBar {
                    background-color: #2c2c2c;
                    border: 1px solid #3c3c3c;
                }
                QStatusBar {
                    background-color: #2c2c2c;
                    color: #f0f0f0;
                }
                QLabel {
                    color: #f0f0f0;
                }
                QPushButton {
                    background-color: #3c3c3c;
                    color: #f0f0f0;
                    border: 1px solid #505050;
                    padding: 5px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #f0f0f0;
                    border: 1px solid #505050;
                    padding: 5px;
                    border-radius: 2px;
                }
                QScrollArea {
                    background-color: #2c2c2c;
                    border: 1px solid #3c3c3c;
                }
                QSlider::groove:horizontal {
                    background: #3c3c3c;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #f0f0f0;
                    width: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QCheckBox {
                    color: #f0f0f0;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #3c3c3c;
                    border: 1px solid #505050;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498DB;
                    border: 1px solid #505050;
                }
            """)
        else:
            # Light theme
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QMenuBar {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu {
                    background-color: #f5f5f5;
                    color: #333333;
                    border: 1px solid #dcdcdc;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                QToolBar {
                    background-color: #f5f5f5;
                    border: 1px solid #dcdcdc;
                }
                QStatusBar {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: #333333;
                    border: 1px solid #dcdcdc;
                    padding: 5px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #dcdcdc;
                    padding: 5px;
                    border-radius: 2px;
                }
                QScrollArea {
                    background-color: #ffffff;
                    border: 1px solid #dcdcdc;
                }
                QSlider::groove:horizontal {
                    background: #dcdcdc;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #3498DB;
                    width: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QCheckBox {
                    color: #333333;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #ffffff;
                    border: 1px solid #dcdcdc;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498DB;
                    border: 1px solid #dcdcdc;
                }
            """)
            
        # Update the chat widget theme
        self.chat_widget.apply_theme(self.settings.get("dark_theme", True))
        
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self, 
            "About Gemini AI Assistant",
            """
            <h1>Gemini AI Assistant</h1>
            <p>A chat application powered by Google's Gemini AI.</p>
            <p>Version 1.0</p>
            <p>&copy; 2023</p>
            """
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Auto save chat history if enabled
        if self.settings.get("auto_save", True):
            self.chat_widget.save_chat_history()
        event.accept()

class AIChatWidget(QWidget):
    """Widget for interacting with the Gemini-powered AI assistant."""
    
    def __init__(self, parent=None):
        """Initialize the chat widget."""
        super().__init__(parent)
        
        # Get settings from parent if available
        self.settings = {}
        if isinstance(parent, ChatMainWindow):
            self.settings = parent.settings
        
        # Initialize the Gemini-powered chatbot
        self.chatbot = SimpleChat(temperature=self.settings.get("temperature", 0.7))
        
        # Selected message for copy operation
        self.selected_message = None
        
        # Setup UI
        self.setup_ui()
        
        # Apply theme
        self.apply_theme(self.settings.get("dark_theme", True))
        
        # Display initial bot message
        initial_messages = self.chatbot.conversation_history
        for message in initial_messages:
            if message["role"] == "assistant":
                self.add_message(message["content"], is_user=False)
        
    def create_message_bubble(self, text, is_user=False):
        """Create a message bubble."""
        # Create main bubble widget
        bubble = QWidget()
        bubble.setObjectName("user-message" if is_user else "message-bubble")
        bubble.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Store the text for copy operations
        bubble.message_text = text
        
        # Create horizontal layout for alignment control
        bubble_layout = QHBoxLayout(bubble)
        bubble_layout.setContentsMargins(2, 2, 2, 2)
        bubble_layout.setSpacing(0)
        
        # Create the actual message container
        message_container = QWidget()
        message_container.setObjectName("message-container")
        
        # Container layout
        container_layout = QVBoxLayout(message_container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(0)
        
        # Replace newlines with HTML line breaks
        formatted_text = text.replace('\n', '<br>')
        
        # Create label with formatted text
        message_label = QLabel(formatted_text)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Add label to container
        container_layout.addWidget(message_label)
        
        # Add timestamp
        timestamp = QLabel(datetime.now().strftime("%H:%M:%S"))
        timestamp.setObjectName("timestamp")
        timestamp.setAlignment(Qt.AlignmentFlag.AlignRight)
        container_layout.addWidget(timestamp)
        
        # Set alignment based on message type
        if is_user:
            bubble_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            bubble_layout.addStretch(1)  # Push content to right
            bubble_layout.addWidget(message_container)
        else:
            bubble_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bubble_layout.addWidget(message_container)
            bubble_layout.addStretch(1)  # Push content to left
        
        # Set size policies
        message_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        message_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        # Add click handler for copying
        bubble.mousePressEvent = lambda event: self.select_message(bubble)
        
        return bubble
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title_layout = QHBoxLayout()
        
        title = QLabel("Gemini AI Assistant")
        title.setObjectName("page-title")
        title.setFont(QFont(self.font().family(), 24, QFont.Weight.Bold))
        title_layout.addWidget(title)
        
        # Clear chat button
        clear_button = QPushButton("Clear Chat")
        clear_button.setObjectName("secondary-button")
        clear_button.clicked.connect(self.clear_chat)
        title_layout.addWidget(clear_button)
        
        layout.addLayout(title_layout)
        
        # Scroll Area for Chat
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("chat-scroll-area")
        self.scroll_area.setMinimumWidth(400)
        self.scroll_area.setMinimumHeight(500)
        
        # Chat area container
        chat_container = QWidget()
        self.chat_layout = QVBoxLayout(chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(chat_container)
        layout.addWidget(self.scroll_area)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        # Message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        # Send button
        send_button = QPushButton("Send")
        send_button.setObjectName("primary-button")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
        
        # Status message (typing indicator, etc.)
        self.status_label = QLabel("")
        self.status_label.setObjectName("status-label")
        layout.addWidget(self.status_label)
        
        # Set up a timer for auto-scrolling
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
        
    def apply_theme(self, dark_mode=True):
        """Apply theme to the chat widget."""
        if dark_mode:
            # Dark theme
            self.setStyleSheet("""
                QLabel#page-title {
                    color: #f0f0f0;
                    margin-bottom: 15px;
                }
                QScrollArea#chat-scroll-area {
                    background-color: #2c2c2c;
                    border: 1px solid #3c3c3c;
                    border-radius: 5px;
                }
                QWidget#message-bubble {
                    background-color: transparent;
                    border: none;
                }
                QWidget#message-container {
                    background-color: #505050;
                    border-radius: 10px;
                    max-width: 400px;
                }
                QLabel {
                    color: #f0f0f0;
                    font-size: 14px;
                    background: transparent;
                }
                QLabel#timestamp {
                    color: #aaaaaa;
                    font-size: 10px;
                    margin-top: 5px;
                }
                QWidget#user-message {
                    background-color: transparent;
                    border: none;
                }
                QWidget#user-message QWidget#message-container {
                    background-color: #3498DB;
                    border-radius: 10px;
                    max-width: 400px;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #f0f0f0;
                    padding: 8px;
                    border: 1px solid #505050;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton#primary-button {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton#primary-button:hover {
                    background-color: #2980B9;
                }
                QPushButton#secondary-button {
                    background-color: #7F8C8D;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                }
                QPushButton#secondary-button:hover {
                    background-color: #95A5A6;
                }
                QLabel#status-label {
                    color: #aaaaaa;
                    font-style: italic;
                    font-size: 12px;
                }
                QLabel#thinking-indicator {
                    color: #aaaaaa;
                    font-style: italic;
                }
                QWidget#selected-message QWidget#message-container {
                    border: 2px solid #f0f0f0;
                }
            """)
        else:
            # Light theme
            self.setStyleSheet("""
                QLabel#page-title {
                    color: #333333;
                    margin-bottom: 15px;
                }
                QScrollArea#chat-scroll-area {
                    background-color: #ffffff;
                    border: 1px solid #dcdcdc;
                    border-radius: 5px;
                }
                QWidget#message-bubble {
                    background-color: transparent;
                    border: none;
                }
                QWidget#message-container {
                    background-color: #f0f0f0;
                    border-radius: 10px;
                    max-width: 400px;
                }
                QLabel {
                    color: #333333;
                    font-size: 14px;
                    background: transparent;
                }
                QLabel#timestamp {
                    color: #888888;
                    font-size: 10px;
                    margin-top: 5px;
                }
                QWidget#user-message {
                    background-color: transparent;
                    border: none;
                }
                QWidget#user-message QWidget#message-container {
                    background-color: #3498DB;
                    border-radius: 10px;
                    max-width: 400px;
                }
                QWidget#user-message QLabel {
                    color: #ffffff;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #333333;
                    padding: 8px;
                    border: 1px solid #dcdcdc;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton#primary-button {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton#primary-button:hover {
                    background-color: #2980B9;
                }
                QPushButton#secondary-button {
                    background-color: #7F8C8D;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                }
                QPushButton#secondary-button:hover {
                    background-color: #95A5A6;
                }
                QLabel#status-label {
                    color: #888888;
                    font-style: italic;
                    font-size: 12px;
                }
                QLabel#thinking-indicator {
                    color: #888888;
                    font-style: italic;
                }
                QWidget#selected-message QWidget#message-container {
                    border: 2px solid #3498DB;
                }
            """)
        
    def add_message(self, text, is_user=False):
        """Add a message to the chat."""
        bubble = self.create_message_bubble(text, is_user)
        self.chat_layout.addWidget(bubble)
        
        # Trigger scroll to bottom after a short delay
        self.scroll_timer.start(100)
        
    def send_message(self):
        """Send a message to the chatbot."""
        message = self.message_input.text().strip()
        if not message:
            return
            
        # Clear input field
        self.message_input.clear()
        
        # Add user message to chat
        self.add_message(message, is_user=True)
        
        # Show "thinking" indicator
        self.status_label.setText("Gemini is thinking...")
        
        # Get response from AI
        QTimer.singleShot(200, lambda: self.get_ai_response(message))
        
    def get_ai_response(self, message):
        """Get a response from the AI."""
        try:
            # Update status
            self.status_label.setText("Generating response...")
            
            # Get response from Gemini
            response = self.chatbot.get_ai_answer(message)
            
            # Add response to chat
            self.add_message(response, is_user=False)
            
            # Clear status
            self.status_label.setText("")
            
        except Exception as e:
            error_message = f"Error getting response: {str(e)}"
            print(error_message)
            self.add_message(f"I'm sorry, I encountered an error: {str(e)}", is_user=False)
            self.status_label.setText("Error occurred!")
        
    def clear_chat(self):
        """Clear the chat history."""
        # Clear UI
        while self.chat_layout.count():
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Reset chatbot
        self.chatbot = SimpleChat(temperature=self.settings.get("temperature", 0.7))
        
        # Display initial bot message
        initial_messages = self.chatbot.conversation_history
        for message in initial_messages:
            if message["role"] == "assistant":
                self.add_message(message["content"], is_user=False)
                
    def select_message(self, message_bubble):
        """Select a message for copying."""
        # Deselect previous selection
        if self.selected_message:
            self.selected_message.setObjectName(
                "user-message" if "user-message" in self.selected_message.objectName() else "message-bubble"
            )
            self.selected_message.setStyleSheet("")
        
        # Select new message
        if self.selected_message == message_bubble:
            self.selected_message = None
        else:
            message_bubble.setObjectName(
                message_bubble.objectName() + " selected-message"
            )
            self.selected_message = message_bubble
            
            # Create a context menu
            menu = QMenu(self)
            copy_action = menu.addAction("Copy")
            copy_action.triggered.connect(lambda: self.copy_message(message_bubble.message_text))
            menu.exec(QGuiApplication.primaryScreen().cursor().pos())
    
    def copy_message(self, text):
        """Copy message text to clipboard."""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        self.status_label.setText("Message copied to clipboard")
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))
        
    def copy_selection(self):
        """Copy selected message to clipboard."""
        if self.selected_message:
            self.copy_message(self.selected_message.message_text)
            
    def save_chat_history(self):
        """Save chat history to a file."""
        try:
            # Get file path
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Chat History", "", "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path:
                return
                
            # Ensure it has .json extension
            if not file_path.endswith(".json"):
                file_path += ".json"
                
            # Save history
            with open(file_path, "w") as f:
                json.dump(self.chatbot.conversation_history, f, indent=2)
                
            self.status_label.setText(f"Chat history saved to {file_path}")
            QTimer.singleShot(2000, lambda: self.status_label.setText(""))
            
        except Exception as e:
            self.status_label.setText(f"Error saving chat history: {str(e)}")
            QTimer.singleShot(2000, lambda: self.status_label.setText(""))
            
    def load_chat_history(self):
        """Load chat history from a file."""
        try:
            # Get file path
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Load Chat History", "", "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path:
                return
                
            # Load history
            with open(file_path, "r") as f:
                history = json.load(f)
                
            # Clear current chat
            self.clear_chat()
            
            # Create new chatbot with loaded history
            self.chatbot = SimpleChat(temperature=self.settings.get("temperature", 0.7))
            
            # Add messages to UI
            for message in history:
                if message["role"] in ["user", "assistant"]:
                    self.add_message(message["content"], is_user=(message["role"] == "user"))
                    
                    # Add to chatbot history
                    if message["role"] == "user":
                        self.chatbot.add_user_message(message["content"])
                    else:
                        self.chatbot.add_bot_message(message["content"])
                        
            self.status_label.setText(f"Chat history loaded from {file_path}")
            QTimer.singleShot(2000, lambda: self.status_label.setText(""))
            
        except Exception as e:
            self.status_label.setText(f"Error loading chat history: {str(e)}")
            QTimer.singleShot(2000, lambda: self.status_label.setText(""))
            
    def update_settings(self, settings):
        """Update settings and apply them."""
        self.settings = settings
        
        # Update chatbot temperature
        self.chatbot.temperature = settings.get("temperature", 0.7)
        
        # Apply theme
        self.apply_theme(settings.get("dark_theme", True)) 