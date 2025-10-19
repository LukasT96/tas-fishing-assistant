# Tasmania Fishing Chatbot - System Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Overall Architecture](#overall-architecture)
3. [RAG Pipeline Architecture](#rag-pipeline-architecture)
4. [Component Details](#component-details)
5. [Data Flow](#data-flow)
6. [Technology Stack](#technology-stack)

---

## System Overview

The Tasmania Fishing Chatbot is an intelligent conversational AI system designed to assist users with fishing-related queries about Tasmania. The system combines Retrieval-Augmented Generation (RAG) with external tool integration to provide accurate, contextual responses about fishing regulations, species information, locations, and weather conditions.

**Key Capabilities:**
- Answer questions about fishing regulations and licenses
- Provide species identification and legal size/bag limits
- Recommend fishing locations across Tasmania
- Retrieve real-time weather forecasts for fishing planning
- Handle casual conversation and general queries

---

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                          │
│                         (Gradio Web App)                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MAIN WINDOW                              │
│                      (app.py / MainWindow)                       │
│                                                                   │
│  • Manages UI components and user interactions                   │
│  • Initializes RAG and Tools models                              │
│  • Loads fishing documents at startup                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                            ROUTER                                │
│                      (router.py / Router)                        │
│                                                                   │
│  Decision Engine: Analyzes queries and routes to:                │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │  RAG Only    │  Tool Only   │ RAG + Tool   │ General Chat │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
└───────────┬──────────────────────────────────────┬──────────────┘
            │                                      │
            ▼                                      ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│      RAG MODEL          │          │     TOOLS MODEL         │
│  (rag_model.py)         │          │  (tools_model.py)       │
│                         │          │                         │
│  • Document retrieval   │          │  • Weather API          │
│  • Vector search        │          │  • External services    │
│  • Context generation   │          │  • Future: More tools   │
└────────┬────────────────┘          └─────────────────────────┘
         │
         ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│   VECTOR DATABASE       │          │      LLM SERVICES       │
│   (ChromaDB)            │          │                         │
│                         │          │  • Groq (fast)          │
│  • Embeddings storage   │          │  • Google Gemini        │
│  • Similarity search    │          │  • Configurable         │
└─────────────────────────┘          └─────────────────────────┘
```

### Architecture Layers

**1. Presentation Layer**
- Gradio-based web interface
- Chat interface with example queries
- Responsive 2-column layout (sidebar + chat)

**2. Application Layer**
- MainWindow: UI orchestration and document loading
- Router: Intelligent query routing and response generation

**3. Business Logic Layer**
- RAG Model: Document retrieval and context management
- Tools Model: External service integration

**4. Data Layer**
- ChromaDB: Vector storage and similarity search
- JSON Documents: Ground truth fishing data
- External APIs: Weather and future services

**5. AI/ML Layer**
- LLM Providers: Groq, Google Gemini
- Embedding Model: Sentence Transformers
- Routing Logic: LLM-powered decision making

---

## RAG Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG PIPELINE FLOW                            │
└─────────────────────────────────────────────────────────────────┘

1. DOCUMENT INGESTION PHASE (Startup)
   ════════════════════════════════════
   
   JSON Documents                    Chunking Strategy
   (fishing_data/*.json)             ─────────────────
         │                           • Chunk size: 300 words
         │                           • Overlap: 50 words
         ▼                           • Section-based splitting
   ┌──────────────┐
   │ JSON Parsing │ ────────────────────────────────┐
   └──────┬───────┘                                 │
          │                                         │
          ▼                                         ▼
   ┌─────────────────┐                    ┌──────────────────┐
   │ Text Conversion │                    │ Metadata         │
   │ (_json_to_text) │                    │ Extraction       │
   └────────┬────────┘                    │                  │
            │                              │ • source         │
            ▼                              │ • section        │
   ┌─────────────────┐                    │ • chunk_id       │
   │ Text Chunking   │                    │ • topics         │
   │ (chunk_text)    │                    └────────┬─────────┘
   └────────┬────────┘                             │
            │                                      │
            └──────────────┬───────────────────────┘
                           ▼
                  ┌─────────────────┐
                  │ Embedding       │
                  │ Generation      │
                  │ (Sentence-BERT) │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Vector Storage  │
                  │ (ChromaDB)      │
                  │                 │
                  │ Collections:    │
                  │ • tasmania_     │
                  │   fishing_docs  │
                  └─────────────────┘


2. QUERY PROCESSING PHASE (Runtime)
   ═════════════════════════════════
   
   User Query
        │
        ▼
   ┌──────────────────┐
   │ Query Analysis   │
   │ & Normalization  │
   │                  │
   │ • Species name   │
   │   normalization  │
   │ • Query intent   │
   │   detection      │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Section Filter   │
   │ Detection        │
   │                  │
   │ Auto-detect:     │
   │ • License        │
   │ • Species        │
   │ • Locations      │
   │ • Seasons        │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Query Embedding  │
   │ (Same model as   │
   │  documents)      │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Vector Search    │
   │ (Similarity)     │
   │                  │
   │ • Cosine         │
   │   similarity     │
   │ • Top-k: 5       │
   │ • Metadata       │
   │   filtering      │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Context Assembly │
   │                  │
   │ Format:          │
   │ [Source: name]   │
   │ Retrieved text   │
   │ ...              │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ LLM Generation   │
   │                  │
   │ Prompt:          │
   │ • Query          │
   │ • Context        │
   │ • Instructions   │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Response         │
   │ Enhancement      │
   │                  │
   │ • Add follow-up  │
   │   suggestions    │
   │ • Interactive    │
   │   elements       │
   └────────┬─────────┘
            │
            ▼
        Response to User
```

### RAG Component Details

**Document Processing:**
- Input: JSON files with structured fishing data
- Sections: fishing_licence, species, fishing_seasons, hot_fishing_spots
- Processing: JSON → Text → Chunks → Embeddings → Vector DB

**Embedding Model:**
- Model: Sentence Transformers (all-MiniLM-L6-v2 or similar)
- Dimensionality: 384 dimensions
- Purpose: Convert text chunks into dense vector representations

**Vector Database (ChromaDB):**
- Storage: In-memory/persistent based on config
- Collection: tasmania_fishing_docs
- Metadata fields:
  - source: Document filename
  - section: fishing_licence, species, etc.
  - chunk_id: Sequential identifier
  - topics: Comma-separated relevant topics

**Retrieval Strategy:**
- Method: Cosine similarity search
- Top-k: 5 most relevant chunks (configurable)
- Filtering: Automatic section detection based on query
- Normalization: Species names standardized for better matching

**Context Generation:**
- Format: Source-attributed chunks
- Structure: [Source: file/section] + content
- Purpose: Provide LLM with relevant background information

---

## Data Flow

### Complete Query Flow

```
1. User Input
   └─> "What's the bag limit for flathead?"

2. Main Window (app.py)
   └─> chat() method receives message

3. Router (router.py)
   ├─> route() analyzes query
   ├─> LLM determines: RAG_ONLY
   └─> execute_route() with RAG_ONLY

4. RAG Model (rag_model.py)
   ├─> Normalize query: "flathead"
   ├─> Detect section filter: "species"
   ├─> search() in vector DB
   ├─> Retrieve top 5 chunks
   └─> Format context

5. LLM Generation
   ├─> Prompt: query + context
   ├─> Generate answer
   └─> Return response

6. Response Enhancement
   ├─> Add follow-up suggestions
   └─> Format for display

7. User sees answer
   └─> "Flathead bag limit is 10 per person..."
```

### Tool Integration Flow

```
1. User Query
   └─> "Will tomorrow be good for fishing in Hobart?"

2. Router Analysis
   ├─> Detects: needs_tool = true
   ├─> Tool: get_fishing_weather
   └─> Params: {location: "Hobart", days: 5}

3. Tools Model
   ├─> Call OpenWeatherMap API
   ├─> Get 5-day forecast
   ├─> Calculate fishing scores
   ├─> Find best day
   └─> Return formatted data

4. Response Generation
   ├─> LLM formats tool data
   ├─> Add recommendations
   └─> Return to user

5. User sees weather + fishing advice
```

### RAG + Tool Combined Flow

```
1. User Query
   └─> "Best spots for flathead and weather this week?"

2. Router Analysis
   ├─> Detects: needs_rag = true
   ├─> Detects: needs_tool = true
   └─> Route: RAG_AND_TOOL

3. Parallel Processing
   ├─> RAG: Search for flathead spots
   └─> Tool: Get weather forecast

4. Integration
   ├─> Combine location context
   ├─> Combine weather data
   └─> LLM synthesizes both

5. User sees: "Best flathead spots + weather suitability"
```

---

## Conclusion

The Tasmania Fishing Chatbot demonstrates a well-architected RAG system that combines document retrieval with external tool integration. The modular design allows for easy maintenance and extension, while the intelligent routing ensures users receive accurate, contextual responses efficiently.

The system successfully balances:
- **Accuracy**: Through grounded RAG responses
- **Freshness**: Via real-time tool integration
- **Usability**: With intelligent routing and interactive UI
- **Maintainability**: Through clean architecture and configuration

This architecture provides a solid foundation for an intelligent, helpful fishing assistant that can grow with user needs.