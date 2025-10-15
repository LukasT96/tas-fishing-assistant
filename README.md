# Tasmania Fishing Information Chatbot

A RAG-powered Q&A system providing information about fishing regulations, species, locations, and licenses in Tasmania. Combines **Retrieval Augmented Generation (RAG)** with **Tool Calling** to deliver accurate, grounded answers.

🎣 **[View Architecture Documentation](ARCHITECTURE.md)**

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Target Users](#target-users)
- [Knowledge Base](#knowledge-base)
- [Tools](#tools)
- [Technology Stack](#technology-stack)
- [How Routing Works](#how-routing-works)
- [Setup & Installation](#setup--installation)
- [Usage Examples](#usage-examples)
- [Evaluation Results](#evaluation-results)
- [Limitations](#limitations)
- [Project Structure](#project-structure)

---

## Overview

The Tasmania Fishing Assistant is an intelligent question-answering system that helps users understand fishing regulations and legal requirements in Tasmania. It uses:

1. **RAG (Retrieval Augmented Generation)**: Searches ~20 pages of official fishing documents to answer regulatory questions
2. **Tool Calling**: Uses a legal size checker to verify if caught fish meet minimum size requirements
3. **Prompt-Driven Routing**: An LLM-based router (no hard-coded rules) intelligently decides when to use documents, tools, or both

The system **always grounds its answers** by citing sources from documents or displaying tool results.

---

## Features

✅ **RAG over Official Documents**: Searches fishing regulations, license info, species guides, and location data  
✅ **Legal Size Verification Tool**: Check if your catch meets minimum legal size  
✅ **Intelligent Routing**: LLM decides whether to use RAG, tools, or both  
✅ **Grounded Answers**: All responses cite sources or tool results  
✅ **Error Handling**: Never crashes - gracefully handles failures  
✅ **User-Friendly UI**: Chat interface built with Gradio  
✅ **Configurable**: All settings in `config.yml`

---

## Target Users

- 🎣 Recreational fishermen in Tasmania
- ✈️ Tourists planning fishing trips
- 📋 Anyone needing quick access to fishing regulations
- 🐟 Anglers wanting to verify legal catch sizes

---

## Knowledge Base

The system uses **~20 pages** of official documentation:

- **Fishing_licences.txt**: License types, fees, requirements
- **General_Guide.txt**: Comprehensive fishing regulations (bag limits, size limits, seasons)
- **Fishing_seasons.txt**: Seasonal closures and restrictions
- **Locations.txt**: Fishing location information

Documents are chunked (300 words, 50-word overlap) and embedded using `all-MiniLM-L6-v2`.

---

## Tools

### Legal Size Checker

Verifies if caught fish meet minimum legal size requirements:

| Species | Minimum Size |
|---------|--------------|
| Brown Trout | 25 cm |
| Rainbow Trout | 25 cm |
| Atlantic Salmon | 30 cm |
| Rock Lobster | 10.5 cm (carapace) |
| Abalone | 11 cm (shell) |

**Usage**: Ask questions like "Is a 28cm brown trout legal to keep?"

---

## Technology Stack

- **LLMs**: Groq (Llama 3.3 70B Versatile) / Google Gemini 2.0 Flash
- **Vector DB**: ChromaDB (in-memory)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`)
- **UI**: Gradio (chat interface)
- **Routing**: Prompt-driven LLM routing (no hard-coded rules)
- **Language**: Python 3.9+

---

## How Routing Works

The system uses **prompt-driven routing** with no hard-coded if/else statements:

1. **User asks a question** → Router receives query
2. **LLM analyzes the question** → Returns JSON decision:
   ```json
   {
     "needs_rag": true/false,
     "needs_tool": true/false,
     "tool_name": "check_legal_size",
     "tool_params": {"species": "brown trout", "length_cm": 28},
     "reasoning": "User wants to verify legal size"
   }
   ```
3. **System executes based on decision**:
   - **RAG only**: Search documents and generate answer
   - **Tool only**: Call tool and return result
   - **Both**: Retrieve documents + call tool, then generate combined answer

**Decision Guidelines** (from prompt):
- Questions about regulations, species info, locations, licenses → **RAG**
- Questions like "is X cm legal" or "can I keep this fish" → **Tool**
- Questions combining both → **RAG + Tool**

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

---

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

Create a file named `.env` in the root directory:
```bash
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_gemini_key_here
```

**5. Run the application:**
```bash
python app.py
```

The app will launch at `http://localhost:7860`

---

## Usage Examples

### Example 1: RAG-Only Query

**User**: "What fishing licence do I need for rock lobster?"

**System Response**:
```
You need a Rock Lobster Pot, Ring or Dive licence. This licence is 
not available to children under 10 years.

Licence Fees (2025-2026):
• Standard Licence: $66.85 for first licence
• Concession Licence: $38.20 for first licence

📚 Source: Fishing_licences (chunk 2)
```

**Routing Decision**: RAG only (retrieved from documents)

---

### Example 2: Tool-Only Query

**User**: "Is a 28cm brown trout legal to keep?"

**System Response**:
```
✅ LEGAL TO KEEP

• Species: Brown Trout
• Your catch: 28 cm
• Legal minimum: 25 cm
• Over limit by: 3.0 cm

This fish meets the legal size requirement and may be kept 
(subject to bag limits).
```

**Routing Decision**: Tool only (legal size checker called)

---

### Example 3: RAG + Tool Query

**User**: "I caught a 32cm Atlantic salmon, can I keep it? What's the bag limit?"

**System Response**:
```
✅ LEGAL TO KEEP

• Species: Atlantic Salmon
• Your catch: 32 cm
• Legal minimum: 30 cm
• Over limit by: 2.0 cm

Your 32cm Atlantic salmon exceeds the minimum legal size and may be kept.

Bag Limit: According to the regulations, the daily bag limit for 
Atlantic salmon is [specific limit from documents].

📚 Source: General_Guide (chunk 45)
🔧 Tool: Legal Size Checker
```

**Routing Decision**: RAG + Tool (documents for bag limit, tool for size verification)

---

## Evaluation Results

### Passing Tests (Baseline)

Tested with **7 ground truth questions** covering RAG, Tool, and Both scenarios:

| Test ID | Type | Question | Result |
|---------|------|----------|--------|
| P1 | RAG | "What are the bag limits for sand flathead?" | ✅ Pass |
| P2 | Tool | "Is a 28cm brown trout legal to keep?" | ✅ Pass |
| P3 | RAG | "What fishing licence do I need for rock lobster?" | ✅ Pass |
| P4 | Both | "I caught a 32cm Atlantic salmon, can I keep it?" | ✅ Pass |
| P5 | RAG | "What is the bag limit for abalone and what size must they be?" | ✅ Pass |
| P6 | Tool | "Can I keep a 24cm rainbow trout?" | ✅ Pass |
| P7 | RAG | "When does the squid spawning closure start on the north coast?" | ✅ Pass |

**Success Rate**: 7/7 (100%) - All passing baseline questions answered correctly with proper citations/tool results.

### Difficult Questions (Known Limitations)

| Test ID | Question | Failure Mode | Analysis |
|---------|----------|--------------|----------|
| D1 | "What's the best bait for flathead in winter?" | Out of Scope | Documents don't contain fishing techniques/bait info |
| D2 | "I caught a 15cm bream, is it legal?" | Tool Limitation | Bream not in legal size tool's species list |
| D3 | "Can I use my wife's unused abalone quota?" | Complex Regulation | Multi-part regulatory question requiring nuanced interpretation |

**Run Evaluation**:
```bash
python evaluation.py
```

Results saved to `evaluation_results.json`.

---

## Limitations

### Current Limitations

1. **Limited Tool Species**
   - Legal size checker only supports 5 species (trout, salmon, lobster, abalone)
   - Many fish species in Tasmania not covered
   - **Mitigation**: System gracefully returns "species not supported" message

2. **Document Coverage Gaps**
   - Documents focus on regulations, not fishing techniques or local knowledge
   - No real-time information (weather, tide, current conditions)
   - **Mitigation**: System clearly states when information is not available

3. **Complex Multi-Part Questions**
   - Struggles with questions requiring multiple reasoning steps
   - May not properly interpret nuanced regulatory edge cases
   - **Mitigation**: Encourages users to verify with official sources

4. **No Conversation History**
   - Each query is processed independently
   - Cannot reference previous questions in conversation
   - **Future Enhancement**: Add conversation memory

5. **Retrieval Quality**
   - Top-K=3 may miss relevant information in longer documents
   - No re-ranking of retrieved chunks
   - **Future Enhancement**: Implement hybrid search and re-ranking

6. **LLM Hallucination Risk**
   - Despite grounding instructions, LLM may occasionally add unsupported details
   - **Mitigation**: Strong prompts emphasizing "ONLY use provided context"

### Out of Scope

The system **does not** provide:
- ❌ Real-time weather or tide information (tool scaffolded but not enabled)
- ❌ Fishing spot recommendations based on conditions
- ❌ Bait or fishing technique advice
- ❌ Species identification from images
- ❌ License purchase functionality (links to official sites only)

---

## Project Structure

```
tas-fishing-assistant/
│
├── app.py                  # Entry point - runs Gradio app
├── config.yml              # System configuration (models, RAG, tools)
├── requirements.txt        # Python dependencies
├── .env                    # API keys (not in repo)
├── README.md               # This file
├── ARCHITECTURE.md         # Detailed system architecture diagrams
├── evaluation.py           # Evaluation framework and tests
│
├── src/
│   ├── main_ui.py          # Gradio UI controller
│   ├── rag_model.py        # Main RAG pipeline and orchestration
│   ├── router.py           # LLM-based routing logic
│   ├── tools_model.py      # Tool implementations (legal size checker)
│   └── prompts.py          # All system prompts and tool descriptions
│
├── data/
│   ├── Fishing_licences.txt
│   ├── General_Guide.txt
│   ├── Fishing_seasons.txt
│   └── Locations.txt
│
└── static/
    └── style.css           # UI styling
```

### Key Files

- **`prompts.py`**: All routing prompts, system prompts, and tool descriptions
- **`config.yml`**: Model settings (LLM, embedding), RAG config (chunk size, top-k), tool settings
- **`router.py`**: Prompt-driven routing logic (no hard-coded rules)
- **`rag_model.py`**: Complete RAG pipeline and answer generation
- **`tools_model.py`**: Tool implementations with error handling
- **`evaluation.py`**: Ground truth tests and failure analysis

---

## Running Evaluation

To test the system with ground truth questions:

```bash
python evaluation.py
```

This will:
1. Run 7 passing baseline tests (RAG, Tool, Both)
2. Run 3 difficult tests (known failure cases)
3. Verify routing decisions, tool calls, and retrieved citations
4. Generate `evaluation_results.json` with detailed results

---

## Future Enhancements

Potential improvements identified during evaluation:

1. **Expand Tool Coverage**: Add more species to legal size checker
2. **Weather API Integration**: Already scaffolded in `tools_model.py`
3. **Hybrid Search**: Combine semantic + keyword search for better retrieval
4. **Re-ranking**: Re-rank retrieved chunks using cross-encoder
5. **Conversation Memory**: Support multi-turn conversations
6. **Query Expansion**: Generate multiple query variations for better recall
7. **User Feedback Loop**: Allow users to rate answers and report errors

---

## Contributing

Contributions welcome! This project can serve as:
- A portfolio piece demonstrating RAG + Tool integration
- A foundation for other QA systems in different domains
- A teaching example of prompt-driven architecture

---

## License

This project is for educational purposes. Fishing regulations are sourced from official Tasmania government documents.

**Disclaimer**: Always verify fishing regulations with official sources at [https://ifs.tas.gov.au/](https://ifs.tas.gov.au/)

---

## Contact

For questions or issues, please open a GitHub issue or contact the maintainer.

**Repository**: [https://github.com/LukasT96/tas-fishing-assistant](https://github.com/LukasT96/tas-fishing-assistant)

