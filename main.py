"""Main entry point for the Gemini-powered AI chatbot application."""

import sys
from PyQt6.QtWidgets import QApplication
from ai_chat import ChatMainWindow

def main():
    """Launch the AI chatbot application."""
    # Create the application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    main_window = ChatMainWindow()
    main_window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 