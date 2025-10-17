"""

Main UI - App Interface for Chatbox

Library:
    - Gradio : Frontend
    
"""

import os
from typing import List, Tuple
import gradio as gr
import yaml

from src.rag_model import RAGModel
from src.prompts import UI_MESSAGES, EXAMPLE_QUERIES

class MainWindow:
    def __init__(self, config_path: str = "config.yml"):
        """ Initialize the chatbot application """
        
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Initialize bot
        self.bot = RAGModel(config_path=config_path)
        
        # Load docs
        self._load_documents()
        
        # UI components
        self.chat_interface = None

    def build(self):
        """Build a simple 2-column UI: left = sidebar, right = default ChatInterface."""        
        welcome_md = """### Welcome
                            I can help you with:

                            - **Regulations** – Fishing rules and restrictions  
                            - **Species info** – Identification and details  
                            - **Locations** – Where to fish in Tasmania  
                            - **Size limits** – Legal minimum sizes  
                            - **Licenses** – Permit requirements  
                            - **Legal size checks** – Check if your catch is legal

                            Ask me anything about fishing in Tasmania!
                            """

        # Show examples on the left as a simple list (right side stays default)
        examples_md = "### Example questions\n" + "\n".join(f"- {q}" for q in EXAMPLE_QUERIES)

        with gr.Blocks(
            title=self.config['ui']['title'],
            theme='JohnSmith9982/small_and_pretty',
            fill_height=True,
            css_paths=["static/style.css"]
        ) as demo:
            with gr.Row(equal_height=True, elem_classes=["app_row"]):
                # === LEFT: sidebar===
                with gr.Column(scale=4, min_width=260):
                    gr.Markdown(f"# {self.config['ui']['title']}")
                    gr.Markdown(self.config['ui']['description'])
                    gr.Markdown(welcome_md)
                    gr.Markdown(examples_md)

                # === RIGHT: ChatInterface ===
                with gr.Column(scale=8, elem_classes=["chat_col", "chat_card"]):
                        gr.ChatInterface(
                            fn=self.chat,
                            type="messages",
                            autofocus=False,
                            title=None,
                            description=None,
                            theme='JohnSmith9982/small_and_pretty',
                            examples=EXAMPLE_QUERIES,
                        )

        self.chat_interface = demo
        return demo
    
    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        import webbrowser
        import threading
        
        if self.chat_interface is None:
            self.build()
        
        # Default launch settings
        launch_settings = {
            "share": False,
            "server_name": "0.0.0.0",
            "server_port": 7860,
            "show_error": True,
            "inbrowser": True,
        }
        
        # Override with user settings
        launch_settings.update(kwargs)
        
        print(f"\n🚀 Launching app on http://localhost:{launch_settings['server_port']}")
        self.chat_interface.launch(**launch_settings)
        
    def chat(self, message, history) -> str:
        """
        Handle chat message and return response
        
        Args:
            message: User's message
            history: Chat history 
            
        Returns:
            Bot's response
        """
        
        if not message.strip():
            return ""
        
        try:
            # Get response from RAG model
            response = self.bot.query(message)
            return response
        except Exception as e:
            error_msg = f"{UI_MESSAGES['error']}\n\n**Error details:** {str(e)}"
            return error_msg
    
    def _load_documents(self):
        base_path = self.config['documents']['base_path']
        sources = self.config['documents']['sources']

        for doc in sources:
            doc_path = os.path.join(base_path, doc)
            if os.path.exists(doc_path):
                try:
                    self.bot.load_ground_truth(doc_path)
                except Exception as e:
                    print(f"Failed to load {doc}: {e}")
            else:
                print(f"File not found: {doc_path}")
        print("All documents loaded")
        