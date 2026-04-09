import chromadb, os, uuid
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

_client = None
_ef = None

def get_client():
    global _client, _ef
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _client, _ef

def get_collection(chat_id: str):
    client, ef = get_client()
    return client.get_or_create_collection(
        name=f"chat_{chat_id}",
        embedding_function=ef
    )

def ingest_text(chat_id: str, text: str, label: str = "document"):
    """Chunk text by logical blocks and store in ChromaDB."""
    collection = get_collection(chat_id)
    # Split into ~500-char chunks on newlines
    lines = text.split("\n")
    chunks, current = [], []
    current_len = 0
    for line in lines:
        current.append(line)
        current_len += len(line)
        if current_len >= 500:
            chunks.append("\n".join(current))
            current, current_len = [], 0
    if current:
        chunks.append("\n".join(current))

    ids = [f"{label}_{uuid.uuid4().hex[:8]}" for _ in chunks]
    collection.add(documents=chunks, ids=ids,
                   metadatas=[{"label": label}] * len(chunks))
    return len(chunks)

def query_rag(chat_id: str, query: str, n_results: int = 5):
    """Retrieve top-N relevant chunks for a query."""
    collection = get_collection(chat_id)
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))
    return results["documents"][0] if results["documents"] else []

def delete_collection(chat_id: str):
    client, _ = get_client()
    try:
        client.delete_collection(f"chat_{chat_id}")
    except Exception:
        pass
