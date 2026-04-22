# AutoStream Agent

A polished submission-ready conversational AI agent for the ServiceHive internship assignment. This project is designed around the exact requirements in the PDF: intent identification, RAG from a local knowledge base, memory across turns, and controlled lead capture through a mock tool.

## What This Agent Does

- classifies user intent into greeting, inquiry, or high-intent lead
- answers product and policy questions from a local Markdown knowledge base
- retains state across multiple turns using LangGraph state
- extracts lead information across turns
- tracks the user's preferred plan when they mention Basic or Pro
- triggers the mock lead capture tool only after name, email, and creator platform are all available
- uses Gemini fallback handling to stay stable during temporary model demand spikes

## Tech Stack

- Python 3.9+
- LangChain
- LangGraph
- Gemini 2.5 Flash Lite with fallback to Gemini 2.0 Flash Lite
- Gemini Embedding 001

## Project Structure

- `app.py`: terminal chat loop
- `graph.py`: LangGraph workflow definition and routing
- `state.py`: typed graph state
- `intent_utils.py`: intent schema, prompts, and fallback heuristics
- `lead_utils.py`: lead extraction, plan tracking, and missing-field prompts
- `rag_utils.py`: local RAG pipeline with Gemini embeddings
- `prompts.py`: reusable LLM prompts
- `tools.py`: mock lead capture tool
- `knowledge_base.md`: local business knowledge base
- `demo_conversation.txt`: step-by-step script for the demo video

## How to Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env`.
4. Add your Gemini key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

5. Run the project:

```bash
python app.py
```

## Architecture Explanation

I chose LangGraph because this assignment is not just a simple chatbot task. The required behavior is a small agentic workflow with routing, memory, retrieval, and tool execution. LangGraph fits that well because it gives explicit control over state and node transitions while still integrating cleanly with retrieval and LLM components. In this project, each user turn passes through a LangGraph flow that first classifies intent, then routes the conversation into one of three paths: greeting, knowledge retrieval, or lead qualification. This makes the system easier to reason about and aligns closely with the assignment’s expected workflow.

State is stored in a typed graph state object that tracks the latest user message, conversation history, detected intent, retrieved knowledge context, collected lead fields, selected plan, and whether a lead has already been captured. That allows the assistant to remember information across 5 to 6 turns, such as when a user first mentions the Pro plan for a YouTube channel and later provides only their name and email. The RAG pipeline uses a local Markdown file, chunking, Gemini embeddings, and similarity-based retrieval to ground answers in local product data. Lead capture is intentionally gated so the mock tool runs only after all required fields are collected.

## WhatsApp Webhook Integration

To integrate this agent with WhatsApp, I would place it behind a backend service with a webhook endpoint connected to the WhatsApp Business API. When a user sends a message on WhatsApp, Meta sends the message payload to the webhook. The backend identifies the user, loads their stored conversation state, and forwards the text into this LangGraph agent. The agent then performs intent routing, retrieval, and lead qualification just as it does in the terminal version. The backend sends the generated reply back through the WhatsApp API. If the lead capture step succeeds, the same backend layer can store the lead in a CRM, database, or internal sales dashboard. This approach keeps messaging transport separate from agent logic and makes the system easy to deploy in a real workflow.

## Evaluation Criteria Mapping

- `Agent reasoning and intent detection`:
  `graph.py` routes each turn into greeting, inquiry, or high-intent flow. `intent_utils.py` uses LLM-based structured classification with a fallback heuristic.

- `Correct use of RAG`:
  `knowledge_base.md` stores the business data locally. `rag_utils.py` chunks the file, creates Gemini embeddings, and retrieves relevant context before answers are generated.

- `Clean state management`:
  `state.py` defines a typed LangGraph state that stores message history, detected intent, retrieved context, collected lead fields, preferred plan, and lead status across turns.

- `Proper tool calling logic`:
  `lead_utils.py` checks for missing fields and asks only for what is still needed. `graph.py` triggers `mock_lead_capture` only after name, email, and platform are all present.

- `Code clarity and structure`:
  Responsibilities are separated by module: routing, prompts, retrieval, extraction, state, and tools.

- `Real-world deployability`:
  The README explains how the same core agent can be connected to WhatsApp using webhook-based message ingestion and response delivery.

## Demo Conversation

Use this exact flow in your screen recording:

```text
User: Hi, tell me about your pricing.
Agent: Answers from the local knowledge base.

User: Does the Pro plan support 4K and captions?
Agent: Answers from retrieved pricing/features context.

User: That sounds good. I want to try the Pro plan for my YouTube channel.
Agent: Detects high intent, stores the preferred plan and platform, and asks only for missing fields.

User: My name is Rahul.
Agent: Remembers YouTube and the Pro plan, then asks only for email.

User: rahul@gmail.com
Agent: Calls mock_lead_capture and confirms success with a short lead summary.
```
