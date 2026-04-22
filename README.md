# AutoStream Agent Assignment

This project is a conversational AI agent built for the ServiceHive internship assignment.

The agent is designed for a fictional SaaS product called AutoStream, which provides automated video editing tools for content creators.

## Features

- Identifies user intent as greeting, inquiry, or high-intent lead
- Answers product and policy questions from a local knowledge base
- Maintains conversation state across multiple turns
- Collects user lead details step by step
- Calls a mock lead capture function only after collecting all required details

## Tech Stack

- Python 3.9+
- LangChain
- LangGraph
- Gemini API
- Local Markdown knowledge base

## Project Files

- `app.py` - main CLI application
- `graph.py` - workflow and routing logic
- `state.py` - stores conversation state
- `intent_utils.py` - intent detection logic
- `lead_utils.py` - lead information extraction and validation
- `rag_utils.py` - retrieval from local knowledge base
- `tools.py` - mock lead capture function
- `knowledge_base.md` - product and policy information
- `demo_conversation.txt` - sample demo flow

## How to Run

1. Create and activate a virtual environment
2. Install dependencies

```bash
pip install -r requirements.txt
Add your API key in a .env file
GEMINI_API_KEY=your_api_key_here
Run the application
python app.py
Architecture
I used LangGraph because this assignment needs a workflow with memory and routing, not just a normal chatbot response loop.

The agent works in three main steps:

Detect the intent of the user message
If it is a product or pricing question, retrieve relevant information from the local knowledge base
If it is a high-intent message, collect missing lead details and call the mock tool only after all required values are available
The state keeps track of:

conversation history
detected intent
name
email
creator platform
selected plan
whether the lead has already been captured
This helps the bot remember previous information and continue the conversation correctly across multiple turns.

WhatsApp Integration
If this agent had to be connected to WhatsApp, I would use the WhatsApp Business API with a webhook.

The webhook would receive user messages, send them to this agent backend, and return the generated response back to WhatsApp. Conversation state could be stored for each user, and captured leads could be sent to a CRM or database.

Demo Flow
Example conversation:

Ask about pricing
Ask whether Pro supports 4K and AI captions
Show interest in trying the Pro plan
Share name, email, and creator platform
Agent captures the lead successfully

After pasting it, run:

```bash
git add README.md
git commit -m "Update README"
git push
