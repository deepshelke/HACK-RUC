"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any

# Request Models
class CreateChatRequest(BaseModel):
    title: Optional[str] = None

class UpdateChatRequest(BaseModel):
    title: Optional[str] = None

class CreateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)
    role: str = Field(..., pattern="^(user|assistant)$")

class UpdateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)

# Response Models
class MessageResponse(BaseModel):
    id: str
    content: str
    role: str
    timestamp: str  # ISO 8601 string
    chatId: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-123",
                "content": "Hello!",
                "role": "user",
                "timestamp": "2024-01-15T10:30:00.000Z",
                "chatId": "chat-123"
            }
        }

class ChatResponse(BaseModel):
    id: str
    title: str
    createdAt: str  # ISO 8601 string
    updatedAt: str  # ISO 8601 string
    lastMessage: Optional[str] = None
    lastMessageAt: Optional[str] = None
    messageCount: int
    userId: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "chat-123",
                "title": "New Chat 1",
                "createdAt": "2024-01-15T10:30:00.000Z",
                "updatedAt": "2024-01-15T10:35:00.000Z",
                "lastMessage": "Hello, how can I help you?",
                "lastMessageAt": "2024-01-15T10:35:00.000Z",
                "messageCount": 5,
                "userId": "anonymous"
            }
        }

# API Response Wrapper
class ApiResponse(BaseModel):
    data: Any
    message: Optional[str] = None
    error: Optional[str] = None

