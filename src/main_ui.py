"""

Main UI - App Interface for Chatbox

Library:
    - Gradio : Frontend
    
"""

import gradio as gr

class MainWindow:
    def __init__(self):
        self.chat_interface = None

    def build(self):
        # Create chat interface
        self.chat_interface = gr.ChatInterface(
            fn=self.chat,
            title="My Chatbot",
            description="Chat with the assistant",
            examples=["Hello!", "How are you?", "Help me with something"],
        )
    
    def launch(self):
        self.chat_interface.launch()
        
    def chat(self, message, history) -> str:
        """        
        Handle chat message
        """
        
        response = f"You said: {message}"
        
        return response