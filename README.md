# Tasmania Fishing Information Chatbot

A RAG-powered Q&A system providing information about fishing regulations, species, locations, and licenses in Tasmania.

## Target Users

- Recreational fishermen in Tasmania
- Tourists planning fishing trips
- Anyone needing quick access to fishing regulations

## Knowledge Base

The system uses ~20 pages of official documentation:
- Inland Fisheries Service regulations
- Species identification guides
- Fishing location information
- Bag and size limit tables
- License requirements

## Tools

**Legal Size Checker**: Verifies if caught fish meet minimum size requirements for:
- Brown Trout (25cm)
- Rainbow Trout (25cm)
- Atlantic Salmon (30cm)
- Rock Lobster (10.5cm carapace)
- Abalone (11cm shell)

## Technology Stack

- **LLMs**: Groq (Llama 3.3) / Google Gemini
- **Vector DB**: ChromaDB
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **UI**: Gradio
- **Routing**: Prompt-based (no hard-coded rules)

## Setup & Installation

### Prerequisites
- Python 3.9+
- API keys for Groq and Google Gemini

### Getting API Keys

1. **Groq API Key**:
   - Sign up at [https://console.groq.com](https://console.groq.com)
   - Navigate to "API Keys" and create a new key
   - Copy and save the key (you won't be able to see it again!)

2. **Google Gemini API Key**:
   - Go to [Google AI Studio](https://aistudio.google.com)
   - Click "Get API Key" and create a new key
   - Copy and save the key

### Installation Steps

**1. Clone the repository:**
```bash
git clone https://github.com/LukasT96/tas-fishing-assistant
cd tas-fishing-assistant
```
**2. Create virtual environment:**
For **Mac/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```
For **Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Create .env file:**
```bash
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_gemini_key_here
```

**5. Run the application:**
```bash
python app.py
```

