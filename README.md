# Trip-Agent
> Multi-agent trip planning system combining LangGraph orchestration with a RAG destination knowledge base. Type a single natural language prompt and receive a complete trip plan grounded in real destination knowledge.
---

## Overview

### Concept

Type _"Plan a 7-day trip to Tokyo in October, budget £2,500, I love street food and hidden temples"_ and get back a complete trip plan — flights, hotels, weather, and a day-by-day itinerary grounded in a RAG knowledge base of 10,000+ destination guides.

### Why this project

- Uses LLMs for what they're actually good at: reasoning over vague preferences, synthesising multiple data sources, producing coherent natural language output
- Covers every critical gap in the AI engineer job market: LangGraph, LangChain, RAG, vector DBs, AI agents, tool use, and LLM APIs — in one coherent project
- Demo-able in interviews: a recruiter can type a prompt and watch agents complete in real time via SSE streaming

### Output from a single prompt

- Top 3 flight options with real prices and timings (Amadeus API)
- Hotel recommendations filtered by budget, location, and rating
- 7-day weather forecast with packing suggestions
- Day-by-day itinerary grounded in WikiVoyage destination knowledge, personalised to stated interests
- Full budget breakdown with currency conversion

---

## Architecture

### Agent flow

```
User prompt
    │
    ▼
Orchestrator agent
(parse intent · extract destination, dates, budget, interests · enrich with REST Countries)
    │
    ├───────────────────────────────────────────────┐
    │                    │              │           │
    ▼                    ▼              ▼           ▼
Flight agent       Hotel agent    Weather agent   Destination RAG agent
(Amadeus)        (Amadeus Hotels) (OpenWeatherMap)  (ChromaDB + LangChain)
                                                         │
                                                         ▼
                                                     ChromaDB
                                                  (WikiVoyage chunks)
    │                    │              │           │
    └───────────────────────────────────────────────┘
                         │
                    state merge
                         │
                         ▼
            Itinerary generator (LLM)
         (GPT-4o · grounded by RAG context)
                         │
                         ▼
                  Budget checker
            (sum costs · FX · flag overruns)
                         │
                         ▼
               Structured trip plan
```

### Key design decisions

- Four agents run **in parallel** as concurrent LangGraph nodes — no sequential bottleneck
- All agents write into a **shared typed state object** — results are available to downstream nodes without explicit passing
- The RAG agent is the only node that reads from a local store rather than a live API
- Conditional edges allow the orchestrator to retry or reroute if an API call fails

---

## RAG Layer

### Knowledge base

**Source:** WikiVoyage XML dump (free, CC BY-SA licensed)

- Download from: `dumps.wikimedia.org`
- Size: ~500MB for the full English dump
- Coverage: 10,000+ destinations worldwide

**Chunking strategy:** Split by section heading, not by character count

```
Every WikiVoyage article has consistent sections:
See · Do · Eat · Drink · Buy · Sleep · Get in · Get around
```

Each section becomes one or more chunks with metadata:

```python
{
  "text": "Tsukiji Outer Market remains the go-to for...",
  "metadata": {
    "destination": "Tokyo",
    "section": "Eat",
    "country": "Japan",
    "region": "Asia"
  }
}
```

**Why section-level chunking matters:** A "best street food in Tokyo" query should retrieve the entire Eat section for Tokyo, not half of it cut off mid-sentence. Semantic coherence at the chunk level is what makes retrieval meaningful.

### Embedding and storage

- **Embedding model:** `text-embedding-3-small` (OpenAI) — cheap and high quality
- **Vector store:** ChromaDB — runs in-process, no account needed, supports metadata filtering
- **Ingestion script:** Python with `xml.etree` for parsing, LangChain document loaders for embedding

### Retrieval at query time

Uses LangChain `SelfQueryRetriever` — translates natural language into semantic search **plus** metadata filter simultaneously:

```
Query: "street food spots in Tokyo"
→ Semantic search over embeddings
→ Metadata filter: destination="Tokyo", section="Eat"
→ Returns top-k most relevant chunks
```

The metadata filter ensures you never retrieve chunks about Kyoto when the user asked about Tokyo.

### How retrieved context enters the prompt

Retrieved chunks land in LangGraph shared state alongside API results. The itinerary generator node builds a single grounded prompt:

```
You are a travel planner. Generate a 7-day itinerary for Tokyo.

User interests: street food, hidden temples  
Budget remaining after flights and hotels: £980  
Weather: mostly sunny, 18–24°C, light rain on day 4

Destination knowledge (use this to ground your recommendations):
---
[Eat]: Tsukiji Outer Market remains the go-to for...
[Eat]: For standing ramen, the alleys around...
[See]: Yanaka is one of Tokyo's few surviving...
---

Flights: [...]  
Hotels: [...]
```

---

## Agent Details

### Orchestrator agent

**Job 1 — parse prompt into structured entities** Makes a single LLM call to extract fields using Pydantic + LangChain `with_structured_output()`:

```python
{
  "destination": "Tokyo",
  "dates": {"start": "2025-10-10", "end": "2025-10-17"},
  "budget": 2500,
  "currency": "GBP",
  "interests": ["street food", "temples"]
}
```

**Job 2 — enrich state before fan-out** Calls REST Countries API to pull currency code, timezone, and language — written into shared state so downstream agents don't each fetch it independently.

> Must handle messy natural language gracefully — "sometime in October, around 2.5k" should map to sensible defaults, not crash.

### Flight agent

- Calls Amadeus Flight Offers Search API
- Returns top 3 options ranked by price, filtered by travel dates and origin
- Writes `{flights: [...]}` into shared state

### Hotel agent

- Calls Amadeus Hotel List + Hotel Offers APIs
- Filters by destination city, check-in/check-out dates, price ceiling
- Returns top 3 options with rating, price per night, and location

### Weather agent

- Calls OpenWeatherMap One Call API 3.0
- Returns 8-day forecast: temperature range, precipitation, conditions
- Used by itinerary generator to suggest packing and flag bad weather days

### Destination RAG agent

- Constructs queries from user's interests + destination
- Runs `SelfQueryRetriever` against ChromaDB with metadata filters
- Writes top-k retrieved chunks into shared state as `destination_context`

### Itinerary generator

- Assembles the full prompt from merged state
- Calls GPT-4o (or Claude) for final generation
- Output: structured day-by-day plan as JSON

### Budget checker

- Sums flight cost + (hotel price per night × nights) + estimated daily spend
- Converts to user's currency via ExchangeRate-API
- Flags if total exceeds stated budget and suggests adjustments

---

## Tech Stack

### Core

|Component|Technology|
|---|---|
|Agent orchestration|LangGraph `StateGraph`|
|RAG pipeline|LangChain `SelfQueryRetriever`|
|Vector store|ChromaDB|
|Embeddings|OpenAI `text-embedding-3-small`|
|LLM|GPT-4o or Claude|
|API layer|FastAPI (SSE streaming)|
|Containerisation|Docker Compose|
|Deployment|Railway (free tier)|

### External APIs (all free tiers)

|API|Purpose|Free limit|
|---|---|---|
|Amadeus for Developers|Flights + hotels|2,000 calls/month|
|OpenWeatherMap|7-day forecast|1,000 calls/day|
|ExchangeRate-API|FX conversion|Free, no card|
|REST Countries|Country metadata|Unlimited, no key|

---

## 3-Week Build Plan

### Week 1 — RAG knowledge base

- [ ] Download WikiVoyage XML dump and write Python parser to extract destination articles by section
- [ ] Chunk articles by section heading, clean text
- [ ] Generate embeddings with `text-embedding-3-small` and store in ChromaDB with metadata
- [ ] Wire up LangChain `SelfQueryRetriever` and test retrieval quality manually for several destinations
- [ ] Get Amadeus sandbox credentials and write flight + hotel API wrapper functions

### Week 2 — LangGraph agent system

- [ ] Build LangGraph `StateGraph` — define typed shared state schema
- [ ] Implement orchestrator node: LLM call with `with_structured_output()` for entity extraction + REST Countries enrichment
- [ ] Implement four parallel agent nodes and connect as concurrent branches
- [ ] Implement itinerary generator node: assemble prompt from merged state, call GPT-4o
- [ ] Implement budget checker node and test full graph end-to-end

### Week 3 — Serving, UI, polish

- [ ] Build FastAPI SSE endpoint — stream agent status updates in real time
- [ ] Build React frontend: prompt input, live agent status indicators, trip plan rendered as structured cards
- [ ] Containerise with Docker Compose (ChromaDB as a persistent volume)
- [ ] Deploy to Railway from GitHub
- [ ] Write README with architecture diagram, example prompts, and live demo link

---

## CV Bullets

```
Built TripForge, a multi-agent AI travel planner using LangGraph's StateGraph 
to orchestrate four parallel agents (flight search, hotel lookup, weather 
forecast, and destination RAG) whose results are merged into a coherent trip 
plan via a final GPT-4o itinerary generation step.
```

```
Constructed a RAG destination knowledge base by parsing the WikiVoyage XML dump 
(10,000+ articles) into section-level chunks, embedding with OpenAI 
text-embedding-3-small, and indexing in ChromaDB with metadata filtering by 
destination and section type; retrieved context is injected into the itinerary 
prompt to ground LLM outputs in local knowledge.
```

```
Integrated Amadeus (flight and hotel search), OpenWeatherMap (7-day forecast), 
and ExchangeRate-API (FX conversion) as LangGraph tool-use nodes, with 
conditional edges handling API failures and retry logic at the orchestration layer.
```

```
Served the pipeline via a FastAPI SSE endpoint enabling real-time agent progress 
streaming; containerised with Docker Compose and deployed to Railway with a 
CI/CD pipeline from GitHub.
```

---

## Gaps This Project Closes

|Gap|Priority|Status|
|---|---|---|
|LangGraph|Critical|✅ Covered|
|LangChain|Critical|✅ Covered|
|RAG|Critical|✅ Covered|
|Vector DB (ChromaDB)|Critical|✅ Covered|
|AI agents|Critical|✅ Covered|
|Tool use|Critical|✅ Covered|
|OpenAI / Anthropic API|Critical|✅ Covered|
|External API integration|Important|✅ Covered|
|LLM fine-tuning|Important|❌ Not covered|
|Cloud (AWS/GCP)|Important|❌ Not covered (swap Railway → EC2 in half a day)|

---

## Future Extensions

- **Fine-tuning:** fine-tune Mistral 7B with LoRA on synthetic travel itinerary data for the itinerary generation step
- **Cloud deployment:** swap Railway for AWS EC2 + S3 — half a day of work once the app runs locally
- **LangGraph human-in-the-loop:** add a checkpoint after flight/hotel results so the user can confirm before the itinerary is generated
- **Personalisation memory:** store past trips in a user profile and retrieve preferences for future queries
- **Re-ranking:** add a cross-encoder reranker on top of ChromaDB retrieval to improve RAG precision