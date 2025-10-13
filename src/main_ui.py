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
        """Build the Gradio interface"""
        
        with gr.Blocks(
            title=self.config['ui']['title'],
            theme=gr.themes.Soft(
                font=["Arial", "sans-serif"], 
                font_mono=["Arial", "monospace"],
                text_size="sm"
            ),
            css_paths=["static/style.css"]
        ) as demo:
            
            # Header
            gr.Markdown(f"### 🎣 {self.config['ui']['title']}")
            gr.Markdown(f"*{self.config['ui']['description']}*")
            
            # Chat interface with welcome message
            chatbot = gr.Chatbot(
                label="Chat",
                height=350,
                avatar_images=(None, None),
                value=[[None, "👋 Welcome! I can help you with:\n\n🎣 Regulations • 🐟 Species info • 📍 Locations • 📏 Size limits • 📋 Licenses • ✅ Legal size checks\n\nAsk me anything about fishing in Tasmania!"]]
            )
            
            # Input area
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Ask me about fishing in Tasmania...",
                    label="Your Question",
                    scale=4,
                    show_label=False
                )
                submit = gr.Button("Send", variant="primary", scale=1)
            
            # Collapsible example questions
            with gr.Accordion("💡 Example Questions", open=False):
                example_btns = []
                with gr.Row():
                    for example in EXAMPLE_QUERIES[:3]:
                        btn = gr.Button(example, size="sm")
                        example_btns.append(btn)
                with gr.Row():
                    for example in EXAMPLE_QUERIES[3:5]:
                        btn = gr.Button(example, size="sm")
                        example_btns.append(btn)
            
            # Event handlers
            def user_message(user_msg, history):
                """Add user message to chat"""
                return "", history + [[user_msg, None]]
            
            def bot_response(history):
                """Get bot response and update chat"""
                user_msg = history[-1][0]
                bot_msg = self.chat(user_msg, history)
                history[-1][1] = bot_msg
                return history
            
            # Wire up events
            msg.submit(user_message, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot_response, chatbot, chatbot
            )
            
            submit.click(user_message, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot_response, chatbot, chatbot
            )
            
            # Example button handlers
            for i, btn in enumerate(example_btns):
                example_text = EXAMPLE_QUERIES[i]
                btn.click(
                    lambda x=example_text: x,
                    None,
                    msg,
                    queue=False
                )
        
        self.chat_interface = demo
        return demo
    
    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        if self.chat_interface is None:
            self.build()
        
        # Default launch settings
        launch_settings = {
            "share": False,
            "server_name": "0.0.0.0",
            "server_port": 7860,
            "show_error": True,
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
        """ Load all fishing documents into the RAG pipeline """
        base_path = self.config['documents']['base_path']
        sources = self.config['documents']['sources']
        
        for doc in sources:
            doc_path = os.path.join(base_path, doc)
            
            if os.path.exists(doc_path):
                try:
                    self.bot.load_ground_truth(doc_path)
                except Exception as e:
                    print("Failed to load {doc}: {e}")
            else:
                print("File not found: {doc_path}")
        
        print("All documents loaded")
        