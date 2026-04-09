# 🪺 llm-nest

> Your local LLM, at home. Private, persistent, and actually remembers.

**llm-nest** is a self-hosted AI chat application that runs entirely on your own hardware. Powered by Ollama, it gives you a clean multi-chat interface with real memory — RAG, conversation summarization, and pinned facts — so your model never forgets what matters.

No cloud. No API bills. No data leaving your machine.

---

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-009688?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## Why llm-nest?

Most local LLM chat apps are thin wrappers — they forget everything after a few messages, choke on large files, and fall apart at scale. llm-nest is built differently.

| Problem | llm-nest Solution |
|---|---|
| Model forgets early context | Rolling summarization keeps history compressed |
| Can't handle 10K lines of code | RAG chunks & retrieves only what's relevant |
| Chats lost on restart | SQLite persists everything |
| Cloud dependency | 100% local via Ollama |
| Hard to access remotely | REST API — works perfectly over ngrok |

---

## Architecture

```
  Linux Server                                    Your Machine
 ┌──────────────────────────┐                  ┌─────────────────────┐
 │                          │   ngrok tunnel   │                     │
 │  Ollama  ←→  FastAPI  ───┼──────────────────┼──→  Streamlit UI    │
 │              :8000       │                  │       :8501         │
 │                          │                  │                     │
 │  ChromaDB  (embeddings)  │                  │  .env               │
 │  SQLite    (chat history) │                  │  BACKEND_URL=...   │
 └──────────────────────────┘                  └─────────────────────┘
```

Backend lives on your Linux server. Frontend runs anywhere — Windows, Mac, another Linux box. They talk over a clean REST API, making ngrok tunneling seamless.

---

## How Memory Works

Every message goes through a four-layer memory pipeline before reaching the model:

```
Your message
     │
     ├── 1. RAG retrieval       → top-6 relevant chunks from ingested code/docs
     ├── 2. Pinned facts        → key info extracted and remembered forever
     ├── 3. Conversation summary → compressed history of older messages
     └── 4. Recent turns        → last 14 messages verbatim
                │
                ▼
        Single system prompt → Ollama → Streamed response
```

This means you can paste 10,000 lines of code, ask about a function 50 messages later, and the model will find it.

---

## Project Structure

```
llm-nest/
├── README.md
├── backend/                  # Runs on Linux server
│   ├── main.py               # FastAPI — all REST endpoints
│   ├── rag.py                # ChromaDB ingestion & semantic retrieval
│   ├── memory.py             # Summarization, pinned facts, prompt builder
│   ├── database.py           # SQLite chat persistence
│   ├── models.py             # Pydantic schemas
│   ├── requirements.txt
│   └── .env
│
└── frontend/                 # Runs on your machine
    ├── app.py                # Streamlit UI
    ├── api_client.py         # REST client
    ├── requirements.txt
    └── .env
```

---

## Getting Started

### Prerequisites

- Linux server with [Ollama](https://ollama.com) installed
- Your model pulled: `ollama pull nemotron-cascade-2:30b`
- [ngrok](https://ngrok.com) account (free tier works)
- Python 3.10+ on both machines

---

### Backend — Linux Server

```bash
git clone https://github.com/YOUR_USERNAME/llm-nest.git
cd llm-nest/backend
pip install -r requirements.txt --break-system-packages
```

Configure `.env`:

```env
OLLAMA_HOST=http://localhost:11434
MODEL_NAME=nemotron-cascade-2:30b
DB_PATH=./chats.db
CHROMA_PATH=./chroma_db
SUMMARY_THRESHOLD=20
```

Start the API server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Expose it via ngrok:

```bash
ngrok http 8000
# → Copy your URL: https://abc123.ngrok-free.app
```

---

### Frontend — Your Machine

```bash
cd llm-nest/frontend
pip install -r requirements.txt
```

Paste your ngrok URL into `.env`:

```env
BACKEND_URL=https://abc123.ngrok-free.app
```

Launch the UI:

```bash
streamlit run app.py
```

Open `http://localhost:8501` — you're in.

---

## Ingesting Code & Documents

Use the sidebar to upload files or paste text directly. Supported formats: `.py` `.js` `.ts` `.java` `.cpp` `.go` `.rs` `.md` `.txt`

Once ingested, the model will reference your code automatically on every relevant query. A `📎 N chunks retrieved` indicator confirms the model can see your documents.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chats` | Create a new chat |
| `GET` | `/chats` | List all chats |
| `PUT` | `/chats/{id}` | Rename a chat |
| `DELETE` | `/chats/{id}` | Delete chat and embeddings |
| `GET` | `/chats/{id}/messages` | Full message history |
| `POST` | `/chats/{id}/ingest` | Ingest code or text into RAG |
| `POST` | `/chats/{id}/stream` | Send a message, receive SSE stream |

---

## Security

ngrok exposes your server publicly. For personal use this is fine. If sharing the URL, add token-based auth to the FastAPI middleware — a 5-line change.

---

<div align="center">
  Built for people who want powerful AI without giving up their data.
</div>