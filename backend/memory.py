import os, json
import ollama as ol
from dotenv import load_dotenv
from database import get_messages, update_summary, update_pinned, get_chat
load_dotenv()

MODEL = os.getenv("MODEL_NAME", "nemotron-cascade-2:30b")
SUMMARY_THRESHOLD = int(os.getenv("SUMMARY_THRESHOLD", 20))

def maybe_summarize(chat_id: str):
    """After every SUMMARY_THRESHOLD messages, compress old ones into a summary."""
    messages = get_messages(chat_id)
    if len(messages) < SUMMARY_THRESHOLD:
        return
    # Summarize all but the last 6 messages
    to_summarize = messages[:-6]
    if not to_summarize:
        return
    text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in to_summarize])
    prompt = (
        "Summarize the following conversation. Preserve ALL key facts, "
        "decisions, code snippets, names, and context. Be detailed:\n\n" + text
    )
    resp = ol.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    summary = resp["message"]["content"]
    update_summary(chat_id, summary)

def extract_pinned(chat_id: str, user_message: str, assistant_reply: str):
    """Extract important facts to pin in memory."""
    prompt = f"""From this exchange, extract any important facts, project names, 
tech stack, user preferences, or key decisions worth remembering long-term.
Return a JSON array of short strings. If nothing important, return [].

User: {user_message}
Assistant: {assistant_reply}

Return ONLY a JSON array, no explanation."""
    try:
        resp = ol.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
        raw = resp["message"]["content"].strip()
        facts = json.loads(raw)
        if not isinstance(facts, list):
            return
        chat = get_chat(chat_id)
        existing = json.loads(chat.get("pinned_memory", "[]"))
        # Keep unique, max 20 pins
        merged = list(dict.fromkeys(existing + facts))[:20]
        update_pinned(chat_id, merged)
    except Exception:
        pass

def build_prompt(chat_id: str, user_message: str, rag_chunks: list) -> list:
    """Build the full message list: system + summary + pinned + RAG + recent history."""
    chat = get_chat(chat_id)
    messages = get_messages(chat_id)
    summary = chat.get("summary", "")
    pinned = json.loads(chat.get("pinned_memory", "[]"))

    system_parts = ["You are a helpful AI assistant with excellent memory."]

    if pinned:
        system_parts.append("\n## Remembered Facts:\n" + "\n".join(f"- {p}" for p in pinned))

    if summary:
        system_parts.append("\n## Earlier Conversation Summary:\n" + summary)

    if rag_chunks:
        system_parts.append("\n## Relevant Context From Documents:\n" +
                            "\n---\n".join(rag_chunks))

    system_msg = {"role": "system", "content": "\n".join(system_parts)}

    # Use only recent messages (last 10) to avoid overflow
    recent = messages[-10:] if len(messages) > 10 else messages
    history = [{"role": m["role"], "content": m["content"]} for m in recent]

    return [system_msg] + history + [{"role": "user", "content": user_message}]
