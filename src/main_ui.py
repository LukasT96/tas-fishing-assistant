"""

Main UI - App Interface for Chatbox

Library:
    - Gradio : Frontend
    
"""

import os
import gradio as gr
import yaml

from src.rag_model import RAGModel
from src.tools_model import ToolsModel
from src.router import Router
from src.prompts import UI_MESSAGES, EXAMPLE_QUERIES

class MainWindow:
    def __init__(self, config_path: str = "config.yml"):
        """ Initialize the chatbot application """
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Initialize bot
        self.rag = RAGModel(config_path=config_path)
        self.tools = ToolsModel(config_path=config_path)
        
        # Initialize Router
        self.router = Router(rag_model=self.rag, tools_model=self.tools, llm_callable=self.rag.llm_call)
        
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
                            - **Weather forecast** - Check which day will be good for fishing

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
                with gr.Column(scale=4, min_width=260, elem_classes=["left_col"]):
                    gr.Markdown(f"# {self.config['ui']['title']}")
                    gr.Markdown(self.config['ui']['description'])
                    gr.Markdown(welcome_md)
                    gr.Markdown(examples_md)

                # === RIGHT: ChatInterface ===
                with gr.Column(scale=8, elem_classes=["chat_col", "chat_card"]):
                    # Small info button (shows welcome modal on mobile)
                    modal_state = gr.State(False)
                    modal_btn = gr.Button(value="ℹ️", elem_id="welcome_btn", elem_classes=["modal_icon"], visible=True)

                    # Welcome modal (hidden by default); will be shown by modal_btn
                    modal_md = gr.Markdown(welcome_md, elem_id="welcome_modal", visible=False)
                    modal_close = gr.Button(value="Close", elem_classes=["modal_close_btn"], visible=False)
                    gr.ChatInterface(
                            fn=self.chat,
                            type="messages",
                            autofocus=False,
                            title=None,
                            description=None,
                            theme='JohnSmith9982/small_and_pretty',
                            examples=EXAMPLE_QUERIES,
                        )
                    # Click handlers: show/hide the welcome modal
                    def toggle_modal(state: bool):
                        """Toggle visibility for the welcome modal."""
                        new_state = not state
                        # show/hide modal and close button using gr.update
                        return gr.update(visible=new_state), gr.update(visible=new_state), new_state

                    # When modal button clicked, toggle modal visibility
                    modal_btn.click(toggle_modal, inputs=[modal_state], outputs=[modal_md, modal_close, modal_state])
                    # Close button hides modal
                    modal_close.click(lambda state: (gr.update(visible=False), gr.update(visible=False), False), inputs=[modal_state], outputs=[modal_md, modal_close, modal_state])

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
            "inbrowser": True,
        }
        
        # Override with user settings
        launch_settings.update(kwargs)
        
        print(f"\n🚀 Launching app on http://localhost:{launch_settings['server_port']}")
        self.chat_interface.launch(**launch_settings)
      
        
    def chat(self, message, history) -> str:
        """ Handle chat message and return response """
        
        if not message.strip():
            return ""
        
        try:
            # Get response from RAG model
            response = self.router.query_with_routing(message)
            return response
        except Exception as e:
            return UI_MESSAGES['error']
    
    
    def _load_documents(self):
        """ Load all fishing documents into the RAG pipeline """
        base_path = self.config['documents']['base_path']
        sources = self.config['documents']['sources']
        
        for doc in sources:
            doc_path = os.path.join(base_path, doc)
            
            if os.path.exists(doc_path):
                try:
                    self.rag.load_ground_truth(doc_path)
                except Exception as e:
                    print(f"Failed to load {doc}: {e}")
            else:
                print(f"File not found: {doc_path}")
        
        print("All documents loaded")
        