"""Chatbot implementation using Google's Gemini API."""
import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

class SimpleChat:
    """A chatbot class that uses Google's Gemini API."""
    
    def __init__(self, temperature=0.7):
        """Initialize the chatbot with Gemini API."""
        print("Initializing Gemini-powered chatbot...")
        
        # Save the temperature parameter
        self.temperature = temperature
        
        # Load environment variables for API key
        load_dotenv()
        
        # Get API key from environment variables or use placeholder
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY not found in environment variables!")
            self.api_key = "YOUR_API_KEY_HERE"  # Replace with your actual API key
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Set up the model with the specified temperature
        generation_config = {
            "temperature": self.temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        # Create the model with generation config
        self.model = genai.GenerativeModel(
            'gemini-pro',
            generation_config=generation_config
        )
        
        # Start a chat session
        self.chat = self.model.start_chat(history=[])
        
        # Initialize conversation history for our UI
        self.conversation_history = []
        
        # Add initial greeting
        initial_greeting = "Hello! I'm your AI assistant powered by Google's Gemini. How can I help you today?"
        self.add_bot_message(initial_greeting)
        print("Chatbot initialization complete")
        
    def add_bot_message(self, message):
        """Add a bot message to the conversation history."""
        self.conversation_history.append({"role": "assistant", "content": message})
        
    def add_user_message(self, message):
        """Add a user message to the conversation history."""
        self.conversation_history.append({"role": "user", "content": message})
    
    def format_response(self, text):
        """Format the response text for better readability."""
        # Remove extra whitespace and newlines
        text = ' '.join(text.split())
        
        # Add proper line breaks for readability (around 50-60 chars per line)
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= 60:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
                
        if current_line:
            lines.append(' '.join(current_line))
            
        return '\n'.join(lines)

    def get_ai_answer(self, user_message):
        """Generate a response to the user's message using Gemini."""
        try:
            print(f"Processing user message: {user_message}")
            
            # Add user message to history
            self.add_user_message(user_message)
            
            # Get response from Gemini API
            response = self.chat.send_message(user_message)
            assistant_response = response.text
            
            print(f"Raw response from Gemini: {assistant_response}")
            
            # Format the response for better readability
            formatted_response = self.format_response(assistant_response)
            print(f"Formatted assistant response: {formatted_response}")
            
            # Add assistant's response to history
            self.add_bot_message(formatted_response)
            
            return formatted_response
        
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            
            # Add error message to history
            self.add_bot_message(f"I'm sorry, I encountered an error: {str(e)}")
            
            return f"I'm sorry, I encountered an error: {str(e)}"
            
    def get_conversation_history(self):
        """Return the conversation history."""
        return self.conversation_history 