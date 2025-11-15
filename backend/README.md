# Fairly Backend API

REST API for the Fairly chat application, built with FastAPI and integrated with a RAG (Retrieval Augmented Generation) system for intelligent responses.

## Features

- ✅ RESTful API with 9 endpoints (chats and messages)
- ✅ MongoDB integration for data persistence
- ✅ AI-powered responses using Google Gemini and Pinecone
- ✅ Automatic chat metadata updates
- ✅ CORS enabled for frontend integration
- ✅ Type-safe with Pydantic models
- ✅ Auto-generated API documentation

## Project Structure

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # MongoDB connection
│   ├── models.py            # Pydantic models
│   ├── create_indexes.py    # Database index creation
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chats.py         # Chat endpoints
│   │   └── messages.py      # Message endpoints
│   └── services/
│       ├── __init__.py
│       ├── chat_service.py  # Chat business logic
│       ├── message_service.py  # Message business logic
│       └── ai_service.py    # AI integration
├── search engine/
│   └── search_engine.py     # RAG search engine
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── run_api.py              # Server startup script
└── README.md               # This file
```

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

The `.env` file is already configured with your credentials. Make sure it contains:

- MongoDB connection details
- Gemini API key
- Pinecone API key and index name
- Search engine configuration
- API configuration (port, host, CORS)

### 3. Create Database Indexes

```bash
python api/create_indexes.py
```

### 4. Start the Server

```bash
python run_api.py
```

Or directly with uvicorn:

```bash
uvicorn api.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Chat Endpoints

- `GET /api/chats` - Get all chats
- `GET /api/chats/{chat_id}` - Get a specific chat
- `POST /api/chats` - Create a new chat
- `PATCH /api/chats/{chat_id}` - Update a chat
- `DELETE /api/chats/{chat_id}` - Delete a chat

### Message Endpoints

- `GET /api/chats/{chat_id}/messages` - Get all messages for a chat
- `POST /api/chats/{chat_id}/messages` - Create a new message (triggers AI response for user messages)
- `PATCH /api/chats/{chat_id}/messages/{message_id}` - Update a message
- `DELETE /api/chats/{chat_id}/messages/{message_id}` - Delete a message

## Response Format

All responses follow this format:

```json
{
  "data": <actual_data>,
  "message": "optional success message",
  "error": "optional error message"
}
```

## Testing

### Using cURL

#### Create a Chat
```bash
curl -X POST http://localhost:8000/api/chats \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}'
```

#### Get All Chats
```bash
curl http://localhost:8000/api/chats
```

#### Create a Message (User)
```bash
curl -X POST http://localhost:8000/api/chats/{chat_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "What are my rights?", "role": "user"}'
```

#### Get Messages
```bash
curl http://localhost:8000/api/chats/{chat_id}/messages
```

## AI Integration

When a user sends a message with `role: "user"`, the API automatically:

1. Saves the user message
2. Generates an AI response using the search engine
3. Saves the assistant response
4. Updates chat metadata (lastMessage, lastMessageAt, messageCount)

The AI service integrates with your existing 3-layer search engine:
- Layer 1: Query processing and vectorization
- Layer 2: Vector similarity search (Pinecone)
- Layer 3: Response generation (Google Gemini)

## Frontend Integration

Update your frontend `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK_API=false
```

## Development

The server runs with auto-reload enabled by default. Any changes to the code will automatically restart the server.

## Production

For production, run without reload:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Or use a production ASGI server like Gunicorn with Uvicorn workers:

```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Troubleshooting

### MongoDB Connection Issues
- Verify `.env` has correct MongoDB credentials
- Check network connectivity to MongoDB Atlas
- Ensure IP whitelist includes your IP address

### Search Engine Not Initializing
- Verify Gemini API key is valid
- Check Pinecone API key and index name
- Ensure all environment variables are set

### CORS Errors
- Verify `CORS_ORIGINS` in `.env` includes your frontend URL
- Check browser console for specific CORS errors

## License

Part of the Fairly application project.

