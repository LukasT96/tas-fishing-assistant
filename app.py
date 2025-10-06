"""

LLM-based Chatbot with Retrieval Augmented Generation (RAG) and Tool Use

This is the app Entry Point. It initializes the chatbot with the specified configuration, 
sets up the necessary components, and starts the chat interface.

"""

from src.main_ui import MainWindow

def main() -> None:
    """
    Main function to initialize and run the chatbot application.
    """
    app = MainWindow()
    app.build()
    app.launch()
    
    return


if __name__ == "__main__":
    main()