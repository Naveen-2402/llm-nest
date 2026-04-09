import os, uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import ollama as ol
import json

from models import ChatCreate, ChatRename, MessageRequest, IngestRequest
from database import (init_db, create_chat, get_all_chats, get_chat,
                      rename_chat, delete_chat, add_message, get_messages,
                      get_message_count)
from rag import ingest_text, query_rag, delete_collection
from memory import build_prompt, maybe_summarize, extract_pinned

load_dotenv()
MODEL = os.getenv("MODEL_NAME", "nemotron-cascade-2:30b")

app = FastAPI(title="Ollama Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# ── Chat CRUD ────────────────────────────────────────────────────────────────

@app.post("/chats")
def create(body: ChatCreate):
    cid = str(uuid.uuid4())[:8]
    create_chat(cid, body.name)
    return {"chat_id": cid, "name": body.name}

@app.get("/chats")
def list_chats():
    return get_all_chats()

@app.get("/chats/{chat_id}")
def get(chat_id: str):
    c = get_chat(chat_id)
    if not c:
        raise HTTPException(404, "Chat not found")
    return c

@app.put("/chats/{chat_id}")
def rename(chat_id: str, body: ChatRename):
    rename_chat(chat_id, body.name)
    return {"status": "ok"}

@app.delete("/chats/{chat_id}")
def delete(chat_id: str):
    delete_chat(chat_id)
    delete_collection(chat_id)
    return {"status": "ok"}

@app.get("/chats/{chat_id}/messages")
def messages(chat_id: str):
    return get_messages(chat_id)

# ── Ingest large text / code ─────────────────────────────────────────────────

@app.post("/chats/{chat_id}/ingest")
def ingest(chat_id: str, body: IngestRequest):
    n = ingest_text(chat_id, body.content, body.label)
    return {"status": "ok", "chunks_stored": n}

# ── Chat (streaming SSE) ─────────────────────────────────────────────────────

@app.post("/chats/{chat_id}/stream")
def chat_stream(chat_id: str, body: MessageRequest):
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")

    rag_chunks = query_rag(chat_id, body.message)
    prompt_msgs = build_prompt(chat_id, body.message, rag_chunks)

    def generate():
        full = ""
        try:
            stream = ol.chat(model=MODEL, messages=prompt_msgs, stream=True)
            for chunk in stream:
                delta = chunk["message"]["content"]
                full += delta
                yield f"data: {json.dumps({'token': delta})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        # Save to DB
        add_message(chat_id, "user", body.message)
        add_message(chat_id, "assistant", full)

        # Background memory tasks
        maybe_summarize(chat_id)
        extract_pinned(chat_id, body.message, full)

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}
