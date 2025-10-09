"""

Main UI - App Interface for Chatbox

Library:
    - Gradio : Frontend
    
"""

import os
from typing import List, Tuple
import gradio as gr
import yaml

from rag_model import RAGModel
from prompts import UI_MESSAGES, EXAMPLE_QUERIES

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
        
        # Custom CSS for better styling
        custom_css = """
        .header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .example-btn {
            margin: 5px;
        }
        """
        
        with gr.Blocks(
            title=self.config['ui']['title'],
            theme=gr.themes.Soft(),
            css=custom_css
        ) as demo:
            
            # Header
            with gr.Row():
                gr.Markdown(f"""
                <div class="header">
                    <h1>🎣 {self.config['ui']['title']}</h1>
                    <p>{self.config['ui']['description']}</p>
                </div>
                """)
            
            # Welcome message
            gr.Markdown(UI_MESSAGES['welcome'])
            
            # Chat interface
            chatbot = gr.Chatbot(
                height=500,
                label="Conversation",
                show_label=False,
                avatar_images=(None, "🤖")
            )
            
            # Input area
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Ask me about fishing in Tasmania...",
                    label="Your Question",
                    scale=4,
                    lines=2
                )
                submit = gr.Button("Send 📤", variant="primary", scale=1)
            
            # Action buttons
            with gr.Row():
                clear = gr.Button("Clear Chat 🗑️")
                retry = gr.Button("Retry Last ↻")
            
            # Example questions
            gr.Markdown("### 💡 Try These Example Questions:")
            
            with gr.Row():
                example_btns = []
                for example in EXAMPLE_QUERIES[:3]:
                    btn = gr.Button(example, size="sm")
                    example_btns.append(btn)
            
            with gr.Row():
                for example in EXAMPLE_QUERIES[3:5]:
                    btn = gr.Button(example, size="sm")
                    example_btns.append(btn)
            
            # Footer info
            with gr.Accordion("ℹ️ About This System", open=False):
                gr.Markdown("""
                ### How It Works
                
                This chatbot combines two powerful techniques:
                
                1. **📚 Retrieval Augmented Generation (RAG)**  
                   Searches through official fishing documents to find accurate information
                   
                2. **🔧 Tool Calling**  
                   Uses specialized tools to check fish size legality
                
                ### Knowledge Base
                - Fishing regulations and rules
                - Species identification guides  
                - Location information
                - Bag and size limit tables
                - License requirements
                
                ### Tools Available
                - **Legal Size Checker**: Verifies if your catch meets minimum size requirements
                
                ### ⚠️ Important
                Always verify critical information with official sources:
                - [Inland Fisheries Service Tasmania](https://ifs.tas.gov.au/)
                - [Marine Fishing Tasmania](https://fishing.tas.gov.au/)
                """)
            
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
            
            clear.click(lambda: None, None, chatbot, queue=False)
            
            # Example button handlers
            for i, btn in enumerate(example_btns):
                btn.click(
                    lambda x=EXAMPLE_QUERIES[i]: (x, []),
                    None,
                    [msg, chatbot],
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
        