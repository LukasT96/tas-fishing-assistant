# Tasmania Fishing Information Chatbot

A RAG-powered Q&A system providing information about fishing regulations, species, locations, licenses, and **weather-based fishing planning** in Tasmania. Combines **Retrieval Augmented Generation (RAG)** with **Weather Tool Calling** to deliver accurate, grounded answers with fishing forecasts and trip planning.

# Website Link: https://fish.longgbot.cv/


🎣 **[View Architecture Documentation](architecture.md)**

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

The Tasmania Fishing Assistant is an intelligent question-answering system that helps users understand fishing regulations, plan fishing trips, and check weather conditions in Tasmania. It uses:

1. **RAG (Retrieval Augmented Generation)**: Searches ~20 pages of official fishing documents to answer regulatory questions
2. **Weather Tool Calling**: Provides multi-day weather forecasts with fishing condition assessments and trip planning recommendations
3. **Prompt-Driven Routing**: An LLM-based router (no hard-coded rules) intelligently decides when to use documents, tools, or both

The system **always grounds its answers** by citing sources from documents or displaying tool results.

---

## Features

✅ **RAG over Official Documents**: Searches fishing regulations, license info, species guides, and location data  
✅ **5-Day Weather Forecasts**: Get detailed weather forecasts with fishing quality scores  
✅ **Fishing Trip Planning**: Find the best days to fish based on weather conditions  
✅ **Intelligent Routing**: LLM decides whether to use RAG, tools, or both  
✅ **Grounded Answers**: All responses cite sources or tool results  
✅ **Error Handling**: Never crashes - gracefully handles failures  
✅ **User-Friendly UI**: Chat interface built with Gradio  
✅ **Configurable**: All settings in `config.yml`

---

## Target Users

- 🎣 Recreational fishermen in Tasmania planning trips
- ✈️ Tourists scheduling fishing activities
- 📋 Anyone needing quick access to fishing regulations
- 🌤️ Anglers wanting weather-optimized fishing plans

---

## Knowledge Base

The system uses **~20 pages** of official documentation (`tas_fishing_guide.json`) includes following section:

- **Fishing_licences**: License types, fees, requirements
- **Species**: Comprehensive fishing regulations (bag limits, size limits, seasons)
- **Fishing_seasons**: Seasonal closures and restrictions
- **Hot_fishing_spots**: Fishing location information

Documents are chunked (300 words, 50-word overlap) and embedded using `all-MiniLM-L6-v2`.

---

## Tools

### Weather Forecast & Trip Planning Tool

Provides **5-day weather forecasts** with fishing condition assessments for Tasmania locations. The system uses OpenWeatherMap API to deliver:

**Features**:
- **Multi-day forecasts** (1-5 days ahead)
- **Fishing quality scores** (0-10 scale) for each day
- **Best fishing day recommendations** based on conditions
- **Detailed weather metrics**: temperature, wind speed, rainfall, humidity
- **Trip planning suggestions** for optimal fishing times

**Fishing Score Calculation**:
The system scores each day based on:
- **Temperature** (ideal: 10-25°C) - up to 4 points
- **Wind Speed** (ideal: < 15 km/h) - up to 3 points  
- **Rainfall** (ideal: < 2mm) - up to 3 points

**Score Ratings**:
- **8-10**: Excellent 🎣✨
- **6-7**: Good 🎣
- **4-5**: Fair ⚠️
- **0-3**: Poor ❌

**Supported Locations**: All major Tasmania fishing locations (Hobart, Launceston, Strahan, Bicheno, St Helens, etc.)

**Usage Examples**:
- "What's the weather forecast for fishing in Hobart this week?"
- "When is the best day to fish in St Helens over the next 5 days?"
- "Should I plan a fishing trip to Strahan this weekend?"
- "What are the fishing conditions in Bicheno for the next 3 days?"

---

## Technology Stack

- **LLMs**: Groq (Llama 3.3 70B Versatile) / Google Gemini 2.0 Flash
- **Vector DB**: ChromaDB (in-memory)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`)
- **Weather API**: OpenWeatherMap API (free tier, 5-day forecast)
- **UI**: Gradio (chat interface)
- **Routing**: Prompt-driven LLM routing 
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
     "tool_name": "get_fishing_weather",
     "tool_params": {"location": "Hobart", "days": 5},
     "reasoning": "User wants weather forecast for trip planning"
   }
   ```
3. **System executes based on decision**:
   - **RAG only**: Search documents and generate answer
   - **Tool only**: Call weather tool and return forecast
   - **Both**: Retrieve documents + call tool, then generate combined answer

**Decision Guidelines** (from prompt):
- Questions about regulations, species info, locations, licenses → **RAG**
- Questions about weather, forecasts, trip planning → **Weather Tool**
- Questions combining both (e.g., "best location to fish this week") → **RAG + Weather Tool**

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

---

## Setup & Installation

### Prerequisites
- Python 3.9+
- API keys for Groq, Google Gemini, and OpenWeatherMap

### Getting API Keys

1. **Groq API Key**:
   - Sign up at [https://console.groq.com](https://console.groq.com)
   - Navigate to "API Keys" and create a new key
   - Copy and save the key in .env

2. **Google Gemini API Key**:
   - Go to [Google AI Studio](https://aistudio.google.com)
   - Click "Get API Key" and create a new key
   - Copy and save the key in .env

3. **Weather API Key**:
   - Go to [OpenWeatherMap](https://openweathermap.org/api)
   - Sign up for a free account
   - Navigate to "API Keys" and copy your key
   - Free tier includes 5-day forecasts (perfect for fishing planning)
   - Copy and save the key in .env

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
WEATHER_API_KEY=your_openweathermap_key_here
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

### Example 2: Weather Tool-Only Query

**User**: "What's the weather forecast for fishing in Hobart this week?"

**System Response**:
```
🌤️ 5-DAY FISHING FORECAST - HOBART

📅 Monday, Oct 20, 2025
• Temperature: 16°C (max 18°C, min 14°C)
• Wind: 12 km/h
• Rain: 0mm
• Conditions: Partly cloudy
• Fishing Score: 9/10 - Excellent 🎣✨

📅 Tuesday, Oct 21, 2025
• Temperature: 15°C (max 17°C, min 13°C)
• Wind: 18 km/h
• Rain: 2mm
• Conditions: Light rain
• Fishing Score: 7/10 - Good 🎣

... [3 more days] ...

🎯 BEST FISHING DAY: Monday, Oct 20
Excellent conditions with light winds and no rain expected!

📊 OVERALL OUTLOOK: Great week ahead for fishing!

🔧 Tool: Weather Forecast API
```

**Routing Decision**: Tool only (weather forecast)

---

### Example 3: RAG + Weather Tool Query

**User**: "I want to fish for flathead this week - where should I go and when are the best conditions?"

**System Response**:
```
🎣 FLATHEAD FISHING PLAN

BEST LOCATIONS (from regulations):
• Sand flathead are commonly found in estuaries and coastal waters
• Popular spots include [locations from documents]
• Bag limit: 10 per person
• Minimum size: 35cm

📚 Source: General_Guide (chunk 28), Locations (chunk 15)

🌤️ WEATHER FORECAST & BEST DAYS:

📅 BEST DAY: Wednesday, Oct 22 (Score: 8/10 - Excellent 🎣✨)
• Temperature: 17°C, Wind: 10 km/h, Rain: 0mm
• Conditions: Clear skies

📅 ALSO GOOD: Thursday, Oct 23 (Score: 7/10 - Good 🎣)
• Temperature: 16°C, Wind: 15 km/h, Rain: 1mm
• Conditions: Partly cloudy

🎯 RECOMMENDATION:
Plan your flathead fishing trip for Wednesday in calm estuaries. 
Perfect weather conditions with light winds and clear skies!

📚 Sources: General_Guide, Locations
🔧 Tool: Weather Forecast API
```

**Routing Decision**: RAG + Weather Tool (documents for species/location info, tool for weather planning)

---

### Example 4: Trip Planning Query

**User**: "Should I plan a fishing trip to Strahan this weekend?"

**System Response**:
```
🌤️ WEEKEND FISHING CONDITIONS - STRAHAN

📅 Saturday, Oct 25
• Temperature: 14°C, Wind: 25 km/h, Rain: 8mm
• Fishing Score: 4/10 - Fair ⚠️
• Conditions: Moderate rain and strong winds expected

📅 Sunday, Oct 26
• Temperature: 15°C, Wind: 20 km/h, Rain: 3mm
• Fishing Score: 6/10 - Good 🎣
• Conditions: Improving - light rain, winds easing

🎯 RECOMMENDATION:
Sunday looks more promising than Saturday. If flexible, consider 
early next week when conditions are forecast to improve further.

Best fishing day in the next 5 days: Tuesday, Oct 28 (Score: 9/10)

🔧 Tool: Weather Forecast API
```

**Routing Decision**: Weather Tool only

---

## Evaluation Results

### Passing Tests (Updated with Weather Focus)

Tested with **8 ground truth questions** covering RAG, Weather Tool, and Combined scenarios:

| Test ID | Question Type | Status | Notes |
|---|---|---|---|
| P1 | RAG | ✅ Pass | Correct answer and citation |
| P2 | RAG | ✅ Pass | Licence requirement correctly identified |
| P3 | RAG | ✅ Pass | Comprehensive regions listed |
| P4 | Tool | ✅ Pass | Accurate single‑day forecast with score |
| P5 | Tool | ✅ Pass | Ranked 5‑day outlook with recommendation |
| P6 | RAG | ✅ Pass | Correct legal‑size reasoning across species |
| P7 | RAG & Tool | ✅ Pass | Species + 5‑day forecast + local rules |
| P8 | RAG & Tool | ✅ Pass | Flathead rules + 5‑day forecast |

**Success Rate**: 7/7 (100%) - All passing baseline questions answered correctly with proper citations/tool results.

### Difficult Questions (Known Limitations)

| Test ID | Failure Type | Expected Behavior | Actual Behavior | Status |
|---|---|---|---|---|
| D1 | Out of Scope | Recognise info unavailable | Correctly identified | ✅ Pass |
| D2 | Complex Regulation | May struggle | Retrieved and synthesised correctly | ✅ Pass |

**Run Evaluation**:
```bash
python evaluation.py
```

Results saved to `evaluation_results.json`.

---

## Limitations

### Current Limitations

1. **Weather Forecast Scope**
   - Limited to 5-day forecasts (OpenWeatherMap free tier)
   - Daily summaries only (no hourly breakdowns)
   - No historical weather data
   - **Mitigation**: System clearly states forecast range and suggests checking official sources for extended forecasts

2. **No Tide Information**
   - Weather tool doesn't include tide times or heights
   - Important factor for coastal fishing not covered
   - **Future Enhancement**: Integrate tide prediction API

3. **Document Coverage Gaps**
   - Documents focus on regulations, not fishing techniques or local knowledge
   - No information about bait, tackle, or fishing methods
   - **Mitigation**: System clearly states when information is not available

4. **Location Coverage**
   - Weather API requires known location names
   - May not recognize very small towns or specific fishing spots
   - **Mitigation**: Returns error with suggestion to try nearby major towns

5. **No Conversation History**
   - Each query is processed independently
   - Cannot reference previous questions in conversation
   - **Future Enhancement**: Add conversation memory

6. **Retrieval Quality**
   - Top-K=3 may miss relevant information in longer documents
   - No re-ranking of retrieved chunks
   - **Future Enhancement**: Implement hybrid search and re-ranking

7. **LLM Hallucination Risk**
   - Despite grounding instructions, LLM may occasionally add unsupported details
   - **Mitigation**: Strong prompts emphasizing "ONLY use provided context"

### Out of Scope

The system **does not** provide:
- ❌ Hourly weather forecasts
- ❌ Tide times and predictions
- ❌ Moon phase information
- ❌ Bait or fishing technique advice
- ❌ Species identification from images
- ❌ License purchase functionality (links to official sites only)
- ❌ Real-time marine conditions (swell, sea temperature)

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
│   ├── tools_model.py      # Tool implementations (weather forecast)
│   └── prompts.py          # All system prompts and tool descriptions
│
├── data/
│   ├── tas_fishing_guide.json
│
└── static/
    └── style.css           # UI styling
```

### Key Files

- **`prompts.py`**: All routing prompts, system prompts, and tool descriptions
- **`config.yml`**: Model settings (LLM, embedding), RAG config (chunk size, top-k), tool settings
- **`router.py`**: Prompt-driven routing logic (no hard-coded rules)
- **`rag_model.py`**: Complete RAG pipeline and answer generation
- **`tools_model.py`**: Weather forecast tool implementation with error handling
- **`evaluation.py`**: Ground truth tests and failure analysis

---

## Running Evaluation

To test the system with ground truth questions:

```bash
python evaluation.py
```

This will:
1. Run 8 passing baseline tests (RAG, Weather Tool, Combined)
2. Run 2 difficult tests (known failure cases)
3. Verify routing decisions, tool calls, and retrieved citations

---

## Future Enhancements

Potential improvements identified during evaluation:

1. **Tide Prediction Tool**: Integrate tide API for coastal fishing planning
2. **Extended Forecasts**: Support 7-14 day forecasts (requires paid API tier)
3. **Hourly Breakdowns**: Add hourly weather data for same-day planning
4. **Moon Phase Data**: Include moon phase for species that are moon-sensitive
5. **Marine Conditions**: Add swell height, sea temperature, water clarity
6. **Hybrid Search**: Combine semantic + keyword search for better retrieval
7. **Re-ranking**: Re-rank retrieved chunks using cross-encoder
8. **Conversation Memory**: Support multi-turn conversations
9. **User Feedback Loop**: Allow users to rate forecast accuracy

---

## Contributing

Contributions welcome! This project can serve as:
- A portfolio piece demonstrating RAG + Weather Tool integration
- A foundation for other location-based planning systems
- A teaching example of prompt-driven architecture

---

## License

This project is for educational purposes. Fishing regulations are sourced from official Tasmania government documents.

**Disclaimer**: Always verify fishing regulations with official sources at [https://ifs.tas.gov.au/](https://ifs.tas.gov.au/)

Weather forecasts are provided by OpenWeatherMap and should be verified with official meteorological services.

---

## Contact

For questions or issues, please open a GitHub issue or contact the maintainer.

**Repository**: [https://github.com/LukasT96/tas-fishing-assistant](https://github.com/LukasT96/tas-fishing-assistant)
