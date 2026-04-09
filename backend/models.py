from pydantic import BaseModel
from typing import Optional

class ChatCreate(BaseModel):
    name: str = "New Chat"

class ChatRename(BaseModel):
    name: str

class MessageRequest(BaseModel):
    chat_id: str
    message: str

class IngestRequest(BaseModel):
    chat_id: str
    content: str
    label: str = "document"

class StreamRequest(BaseModel):
    chat_id: str
    message: str
