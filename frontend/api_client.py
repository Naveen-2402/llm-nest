import os, requests, sseclient
from dotenv import load_dotenv
load_dotenv()

BASE = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

def create_chat(name="New Chat"):
    return requests.post(f"{BASE}/chats", json={"name": name}).json()

def list_chats():
    return requests.get(f"{BASE}/chats").json()

def rename_chat(chat_id, name):
    requests.put(f"{BASE}/chats/{chat_id}", json={"name": name})

def delete_chat(chat_id):
    requests.delete(f"{BASE}/chats/{chat_id}")

def get_messages(chat_id):
    return requests.get(f"{BASE}/chats/{chat_id}/messages").json()

def ingest(chat_id, content, label="document"):
    return requests.post(
        f"{BASE}/chats/{chat_id}/ingest",
        json={"chat_id": chat_id, "content": content, "label": label},
        timeout=120
    ).json()

def stream_chat(chat_id, message):
    """Yields tokens via SSE streaming."""
    resp = requests.post(
        f"{BASE}/chats/{chat_id}/stream",
        json={"chat_id": chat_id, "message": message},
        stream=True, timeout=300
    )
    client = sseclient.SSEClient(resp)
    for event in client.events():
        import json
        data = json.loads(event.data)
        if "token" in data:
            yield data["token"]
        if data.get("done"):
            break