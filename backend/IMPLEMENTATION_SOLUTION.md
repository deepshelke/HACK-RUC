# Backend Implementation Solution - Fairly Chat Application

## Current State Analysis

### Existing Infrastructure ✅
1. **RAG System**: 3-layer search engine (`search engine/search_engine.py`)
   - Layer 1: Query processing and vectorization
   - Layer 2: Vector similarity search (Pinecone)
   - Layer 3: Response generation (Google Gemini)
   - Uses MongoDB for document storage
   - Uses Pinecone for vector search

2. **Data Processing**: Scripts for processing PDFs and generating embeddings
3. **Dependencies**: Already have MongoDB, Pinecone, and Gemini API setup

### What's Missing ❌
1. **REST API Server**: No HTTP server to handle frontend requests
2. **Chat/Message Storage**: No database schema for chats and messages
3. **API Endpoints**: Need to implement 9 endpoints from `BACKEND_INTEGRATION_PLAN.md`
4. **Integration**: Need to connect search engine to chat API

---

## Recommended Solution Architecture

```
backend/
├── api/                          # NEW: REST API server
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── models.py                # Pydantic models for request/response
│   ├── database.py              # MongoDB connection & utilities
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chats.py             # Chat endpoints
│   │   └── messages.py         # Message endpoints
│   └── services/
│       ├── __init__.py
│       ├── chat_service.py      # Chat business logic
│       ├── message_service.py   # Message business logic
│       └── ai_service.py        # Integration with search engine
├── search engine/                # EXISTING: Keep as is
│   └── search_engine.py
├── data-preprocessing/            # EXISTING: Keep as is
├── embdedding/                   # EXISTING: Keep as is
├── requirements.txt              # UPDATE: Add FastAPI, uvicorn
├── .env                          # UPDATE: Add API port config
└── BACKEND_INTEGRATION_PLAN.md  # EXISTING: API specification
```

---

## Step-by-Step Implementation Plan

### Phase 1: Setup API Infrastructure (30 minutes)

#### 1.1 Update `requirements.txt`
Add FastAPI and related dependencies:
```txt
# Existing dependencies...
pymongo>=4.6.0
pinecone-client>=3.0.0
python-dotenv>=1.0.0
google-generativeai>=0.3.0
pdfplumber>=0.10.0

# NEW: API Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
python-multipart>=0.0.6
```

#### 1.2 Create API Directory Structure
```bash
mkdir -p backend/api/routes
mkdir -p backend/api/services
```

#### 1.3 Update `.env` file
Add API configuration:
```env
# Existing variables...
MONGODB_USERNAME=...
MONGODB_PASSWORD=...
# ... other existing vars ...

# NEW: API Configuration
API_PORT=8000
API_HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000
```

---

### Phase 2: Create Database Models & Connection (45 minutes)

#### 2.1 Create `api/database.py`
```python
"""
MongoDB connection and database utilities.
"""
from pymongo import MongoClient
from urllib.parse import quote_plus
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# MongoDB connection details
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_APP_NAME = os.getenv('MONGODB_APP_NAME')
DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'fairly')

# Collections
CHATS_COLLECTION = 'chats'
MESSAGES_COLLECTION = 'messages'

class Database:
    _client = None
    _db = None
    
    @classmethod
    def connect(cls):
        """Connect to MongoDB."""
        if cls._client is None:
            password_encoded = quote_plus(MONGODB_PASSWORD)
            connection_string = f"mongodb+srv://{MONGODB_USERNAME}:{password_encoded}@{MONGODB_CLUSTER}/?appName={MONGODB_APP_NAME}"
            
            cls._client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True
            )
            cls._db = cls._client[DATABASE_NAME]
            print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
        
        return cls._db
    
    @classmethod
    def get_collection(cls, collection_name):
        """Get a collection."""
        if cls._db is None:
            cls.connect()
        return cls._db[collection_name]
    
    @classmethod
    def close(cls):
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

# Initialize connection
Database.connect()
```

#### 2.2 Create Database Indexes Script
Create `api/create_indexes.py`:
```python
"""
Create indexes for chats and messages collections.
"""
from api.database import Database

def create_indexes():
    """Create necessary indexes."""
    chats_collection = Database.get_collection('chats')
    messages_collection = Database.get_collection('messages')
    
    # Indexes for chats
    chats_collection.create_index("userId")
    chats_collection.create_index("updatedAt")
    
    # Indexes for messages
    messages_collection.create_index("chatId")
    messages_collection.create_index([("chatId", 1), ("timestamp", 1)])
    
    print("✅ Indexes created")

if __name__ == "__main__":
    create_indexes()
```

---

### Phase 3: Create Pydantic Models (30 minutes)

#### 3.1 Create `api/models.py`
```python
"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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
    data: any
    message: Optional[str] = None
    error: Optional[str] = None
```

---

### Phase 4: Create Service Layer (1-2 hours)

#### 4.1 Create `api/services/chat_service.py`
```python
"""
Chat service for business logic.
"""
from api.database import Database, CHATS_COLLECTION
from datetime import datetime
from typing import List, Optional
import uuid
from bson import ObjectId

def generate_id() -> str:
    """Generate unique ID."""
    return str(uuid.uuid4())

def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string."""
    return dt.isoformat() + 'Z'

class ChatService:
    @staticmethod
    def get_all_chats() -> List[dict]:
        """Get all chats."""
        collection = Database.get_collection(CHATS_COLLECTION)
        chats = list(collection.find().sort("updatedAt", -1))
        
        # Convert ObjectId to string and format dates
        for chat in chats:
            chat['id'] = str(chat.pop('_id'))
            chat['createdAt'] = to_iso_string(chat['createdAt'])
            chat['updatedAt'] = to_iso_string(chat['updatedAt'])
            if chat.get('lastMessageAt'):
                chat['lastMessageAt'] = to_iso_string(chat['lastMessageAt'])
        
        return chats
    
    @staticmethod
    def get_chat_by_id(chat_id: str) -> Optional[dict]:
        """Get chat by ID."""
        collection = Database.get_collection(CHATS_COLLECTION)
        chat = collection.find_one({"_id": ObjectId(chat_id)})
        
        if not chat:
            return None
        
        chat['id'] = str(chat.pop('_id'))
        chat['createdAt'] = to_iso_string(chat['createdAt'])
        chat['updatedAt'] = to_iso_string(chat['updatedAt'])
        if chat.get('lastMessageAt'):
            chat['lastMessageAt'] = to_iso_string(chat['lastMessageAt'])
        
        return chat
    
    @staticmethod
    def create_chat(title: Optional[str] = None) -> dict:
        """Create a new chat."""
        collection = Database.get_collection(CHATS_COLLECTION)
        now = datetime.utcnow()
        
        if not title:
            # Generate default title
            count = collection.count_documents({})
            title = f"New Chat {count + 1}"
        
        chat = {
            "_id": ObjectId(),
            "title": title,
            "createdAt": now,
            "updatedAt": now,
            "messageCount": 0,
            "userId": "anonymous"
        }
        
        collection.insert_one(chat)
        chat['id'] = str(chat.pop('_id'))
        chat['createdAt'] = to_iso_string(chat['createdAt'])
        chat['updatedAt'] = to_iso_string(chat['updatedAt'])
        
        return chat
    
    @staticmethod
    def update_chat(chat_id: str, updates: dict) -> Optional[dict]:
        """Update a chat."""
        collection = Database.get_collection(CHATS_COLLECTION)
        updates['updatedAt'] = datetime.utcnow()
        
        result = collection.find_one_and_update(
            {"_id": ObjectId(chat_id)},
            {"$set": updates},
            return_document=True
        )
        
        if not result:
            return None
        
        result['id'] = str(result.pop('_id'))
        result['createdAt'] = to_iso_string(result['createdAt'])
        result['updatedAt'] = to_iso_string(result['updatedAt'])
        if result.get('lastMessageAt'):
            result['lastMessageAt'] = to_iso_string(result['lastMessageAt'])
        
        return result
    
    @staticmethod
    def delete_chat(chat_id: str) -> bool:
        """Delete a chat."""
        collection = Database.get_collection(CHATS_COLLECTION)
        result = collection.delete_one({"_id": ObjectId(chat_id)})
        return result.deleted_count > 0
    
    @staticmethod
    def update_chat_metadata(chat_id: str, last_message: str, message_count: int):
        """Update chat metadata after message operations."""
        collection = Database.get_collection(CHATS_COLLECTION)
        now = datetime.utcnow()
        
        collection.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$set": {
                    "lastMessage": last_message[:100] if last_message else None,
                    "lastMessageAt": now,
                    "updatedAt": now,
                    "messageCount": message_count
                }
            }
        )
```

#### 4.2 Create `api/services/message_service.py`
```python
"""
Message service for business logic.
"""
from api.database import Database, MESSAGES_COLLECTION, CHATS_COLLECTION
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from api.services.chat_service import ChatService

def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string."""
    return dt.isoformat() + 'Z'

class MessageService:
    @staticmethod
    def get_messages_by_chat_id(chat_id: str) -> List[dict]:
        """Get all messages for a chat."""
        collection = Database.get_collection(MESSAGES_COLLECTION)
        messages = list(collection.find({"chatId": chat_id}).sort("timestamp", 1))
        
        for message in messages:
            message['id'] = str(message.pop('_id'))
            message['timestamp'] = to_iso_string(message['timestamp'])
        
        return messages
    
    @staticmethod
    def create_message(chat_id: str, content: str, role: str) -> dict:
        """Create a new message."""
        collection = Database.get_collection(MESSAGES_COLLECTION)
        now = datetime.utcnow()
        
        message = {
            "_id": ObjectId(),
            "content": content,
            "role": role,
            "timestamp": now,
            "chatId": chat_id
        }
        
        collection.insert_one(message)
        
        # Update chat metadata
        messages = MessageService.get_messages_by_chat_id(chat_id)
        ChatService.update_chat_metadata(chat_id, content, len(messages))
        
        message['id'] = str(message.pop('_id'))
        message['timestamp'] = to_iso_string(message['timestamp'])
        
        return message
    
    @staticmethod
    def update_message(chat_id: str, message_id: str, content: str) -> Optional[dict]:
        """Update a message."""
        collection = Database.get_collection(MESSAGES_COLLECTION)
        
        result = collection.find_one_and_update(
            {"_id": ObjectId(message_id), "chatId": chat_id},
            {"$set": {"content": content}},
            return_document=True
        )
        
        if not result:
            return None
        
        # Update chat's lastMessage if this is the last message
        messages = MessageService.get_messages_by_chat_id(chat_id)
        if messages and messages[-1]['id'] == message_id:
            ChatService.update_chat_metadata(chat_id, content, len(messages))
        
        result['id'] = str(result.pop('_id'))
        result['timestamp'] = to_iso_string(result['timestamp'])
        
        return result
    
    @staticmethod
    def delete_message(chat_id: str, message_id: str) -> bool:
        """Delete a message."""
        collection = Database.get_collection(MESSAGES_COLLECTION)
        result = collection.delete_one({"_id": ObjectId(message_id), "chatId": chat_id})
        
        if result.deleted_count > 0:
            # Update chat metadata
            messages = MessageService.get_messages_by_chat_id(chat_id)
            if messages:
                last_message = messages[-1]['content']
                ChatService.update_chat_metadata(chat_id, last_message, len(messages))
            else:
                # No messages left, clear lastMessage
                ChatService.update_chat_metadata(chat_id, "", 0)
        
        return result.deleted_count > 0
```

#### 4.3 Create `api/services/ai_service.py`
```python
"""
AI service to integrate with search engine.
"""
import sys
from pathlib import Path

# Add search engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search engine"))
from search_engine import SearchEngine

class AIService:
    _engine = None
    
    @classmethod
    def get_engine(cls):
        """Get or initialize search engine."""
        if cls._engine is None:
            cls._engine = SearchEngine()
        return cls._engine
    
    @staticmethod
    def generate_response(user_message: str, jurisdiction: str = None) -> str:
        """Generate AI response using search engine."""
        try:
            engine = AIService.get_engine()
            result = engine.search(user_message, jurisdiction)
            
            if result.get("success") and result.get("response"):
                return result["response"]
            else:
                return result.get("message", "I apologize, but I couldn't generate a response. Please try again.")
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "I apologize, but I encountered an error. Please try again."
```

---

### Phase 5: Create API Routes (1 hour)

#### 5.1 Create `api/routes/chats.py`
```python
"""
Chat endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from api.models import (
    CreateChatRequest, UpdateChatRequest, ChatResponse, ApiResponse
)
from api.services.chat_service import ChatService

router = APIRouter(prefix="/api/chats", tags=["chats"])

@router.get("", response_model=ApiResponse)
async def get_all_chats():
    """Get all chats."""
    try:
        chats = ChatService.get_all_chats()
        return {"data": chats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{chat_id}", response_model=ApiResponse)
async def get_chat(chat_id: str):
    """Get a specific chat."""
    chat = ChatService.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return {"data": chat}

@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(request: CreateChatRequest):
    """Create a new chat."""
    try:
        chat = ChatService.create_chat(request.title)
        return {"data": chat}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.patch("/{chat_id}", response_model=ApiResponse)
async def update_chat(chat_id: str, request: UpdateChatRequest):
    """Update a chat."""
    updates = {}
    if request.title is not None:
        updates["title"] = request.title
    
    chat = ChatService.update_chat(chat_id, updates)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return {"data": chat}

@router.delete("/{chat_id}", response_model=ApiResponse)
async def delete_chat(chat_id: str):
    """Delete a chat."""
    # Also delete all messages
    from api.services.message_service import MessageService
    messages = MessageService.get_messages_by_chat_id(chat_id)
    for message in messages:
        MessageService.delete_message(chat_id, message['id'])
    
    deleted = ChatService.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return {"data": None}
```

#### 5.2 Create `api/routes/messages.py`
```python
"""
Message endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from api.models import (
    CreateMessageRequest, UpdateMessageRequest, MessageResponse, ApiResponse
)
from api.services.message_service import MessageService
from api.services.ai_service import AIService

router = APIRouter(prefix="/api/chats", tags=["messages"])

@router.get("/{chat_id}/messages", response_model=ApiResponse)
async def get_messages(chat_id: str):
    """Get all messages for a chat."""
    try:
        messages = MessageService.get_messages_by_chat_id(chat_id)
        return {"data": messages}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{chat_id}/messages", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_message(chat_id: str, request: CreateMessageRequest):
    """Create a new message."""
    try:
        # Create user message
        message = MessageService.create_message(
            chat_id, request.content, request.role
        )
        
        # If it's a user message, generate assistant response
        if request.role == "user":
            # Generate AI response
            ai_response = AIService.generate_response(request.content)
            
            # Create assistant message
            assistant_message = MessageService.create_message(
                chat_id, ai_response, "assistant"
            )
            
            return {"data": message}  # Return user message, assistant is saved
        
        return {"data": message}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.patch("/{chat_id}/messages/{message_id}", response_model=ApiResponse)
async def update_message(chat_id: str, message_id: str, request: UpdateMessageRequest):
    """Update a message."""
    message = MessageService.update_message(chat_id, message_id, request.content)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return {"data": message}

@router.delete("/{chat_id}/messages/{message_id}", response_model=ApiResponse)
async def delete_message(chat_id: str, message_id: str):
    """Delete a message."""
    deleted = MessageService.delete_message(chat_id, message_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return {"data": None}
```

---

### Phase 6: Create Main FastAPI Application (30 minutes)

#### 6.1 Create `api/main.py`
```python
"""
FastAPI main application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chats, messages
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

app = FastAPI(
    title="Fairly Chat API",
    description="REST API for Fairly chat application",
    version="1.0.0"
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chats.router)
app.include_router(messages.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Fairly Chat API", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
```

---

### Phase 7: Create Startup Scripts (15 minutes)

#### 7.1 Create `api/__init__.py`
```python
# API package
```

#### 7.2 Create `api/routes/__init__.py`
```python
# Routes package
```

#### 7.3 Create `api/services/__init__.py`
```python
# Services package
```

#### 7.4 Create `run_api.py` (in backend root)
```python
#!/usr/bin/env python3
"""
Run the FastAPI server.
"""
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True  # Auto-reload on code changes
    )
```

---

## Implementation Checklist

### Setup
- [ ] Update `requirements.txt` with FastAPI dependencies
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create API directory structure
- [ ] Update `.env` with API configuration

### Database
- [ ] Create `api/database.py`
- [ ] Run `api/create_indexes.py` to create indexes
- [ ] Test MongoDB connection

### Models & Services
- [ ] Create `api/models.py` with Pydantic models
- [ ] Create `api/services/chat_service.py`
- [ ] Create `api/services/message_service.py`
- [ ] Create `api/services/ai_service.py` (integrate search engine)

### Routes
- [ ] Create `api/routes/chats.py` with 5 endpoints
- [ ] Create `api/routes/messages.py` with 4 endpoints
- [ ] Create `api/main.py` with FastAPI app

### Testing
- [ ] Test all endpoints with cURL/Postman
- [ ] Verify response formats match spec
- [ ] Test AI response generation
- [ ] Test error handling

### Integration
- [ ] Update frontend `.env.local` with backend URL
- [ ] Test frontend-backend integration
- [ ] Verify CORS works correctly

---

## Running the API

### Development
```bash
cd backend
python run_api.py
```

Or directly:
```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

### Production
```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Testing Endpoints

### Create Chat
```bash
curl -X POST http://localhost:8000/api/chats \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}'
```

### Get All Chats
```bash
curl http://localhost:8000/api/chats
```

### Create Message (User)
```bash
curl -X POST http://localhost:8000/api/chats/{chat_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "What are my rights?", "role": "user"}'
```

### Get Messages
```bash
curl http://localhost:8000/api/chats/{chat_id}/messages
```

---

## Key Integration Points

1. **Search Engine Integration**: The `AIService` wraps your existing `SearchEngine` class
2. **MongoDB**: Reuses your existing MongoDB connection setup
3. **Environment Variables**: Uses your existing `.env` file structure
4. **Response Format**: Matches `BACKEND_INTEGRATION_PLAN.md` exactly

---

## Next Steps After Implementation

1. **Test thoroughly** with frontend
2. **Add error logging** (consider using Python's `logging` module)
3. **Add request validation** (Pydantic handles this)
4. **Monitor performance** (consider adding response time logging)
5. **Add rate limiting** (if needed for production)

---

## Estimated Time

- **Phase 1**: 30 minutes
- **Phase 2**: 45 minutes
- **Phase 3**: 30 minutes
- **Phase 4**: 1-2 hours
- **Phase 5**: 1 hour
- **Phase 6**: 30 minutes
- **Phase 7**: 15 minutes

**Total**: ~4-5 hours for complete implementation

---

## Notes

- All dates are stored as `datetime` objects in MongoDB and converted to ISO 8601 strings in responses
- Chat IDs and Message IDs use MongoDB's `ObjectId` converted to strings
- The AI service initializes the search engine on first use (lazy loading)
- CORS is configured to allow frontend origin
- Error handling follows the API specification format

