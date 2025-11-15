# Fairly - Complete Project Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Frontend Detailed Explanation](#frontend-detailed-explanation)
4. [Backend Explanation](#backend-explanation)
5. [How Frontend and Backend Work Together](#how-frontend-and-backend-work-together)
6. [Technology Stack](#technology-stack)
7. [Project Structure](#project-structure)
8. [Setup Instructions](#setup-instructions)

---

## 🎯 Project Overview

**Fairly** is an AI-powered chat application designed to help domestic workers understand their legal rights. The application uses a sophisticated **RAG (Retrieval Augmented Generation)** system to provide accurate, context-aware responses based on legal documents and regulations.

### Key Features
- 💬 **Intelligent Chat Interface**: Natural conversation with an AI assistant
- 📚 **RAG-Powered Responses**: Answers based on real legal documents
- 🎨 **Customizable Themes**: Multiple visual themes (Caffeine, Neo Brutalism) with light/dark modes
- 💾 **Persistent Chat History**: All conversations are saved and accessible
- 🔍 **Smart Search**: 3-layer search engine for accurate information retrieval
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

### What Problem Does It Solve?
Domestic workers often lack easy access to information about their legal rights. Fairly bridges this gap by:
- Providing instant answers to legal questions
- Sourcing information from verified legal documents
- Supporting multiple jurisdictions (US Federal, NY, NJ, NYC, Philadelphia)
- Offering a user-friendly interface that doesn't require legal expertise

---

## 🏗️ Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FRONTEND (Next.js Application)               │  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │   React UI   │  │   Context    │  │   API Client  │  │  │
│  │  │  Components  │  │   Providers  │  │   (HTTP)      │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  │                                                           │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │ HTTP Requests                        │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI REST API)                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Routes     │  │   Services   │  │   Models     │        │
│  │  (Endpoints) │  │ (Business    │  │  (Data       │        │
│  │              │  │   Logic)     │  │   Schemas)    │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                  │                 │
└─────────┼─────────────────┼──────────────────┼─────────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│   MongoDB       │  │   Pinecone   │  │  Google      │
│   (Database)    │  │  (Vector DB) │  │  Gemini API   │
│                 │  │              │  │              │
│  - Chats        │  │  - Embeddings│  │  - AI        │
│  - Messages    │  │  - Similarity │  │    Responses │
│  - Metadata    │  │    Search     │  │  - Embeddings│
└─────────────────┘  └──────────────┘  └──────────────┘
```

### Data Flow Diagram

```
User Types Message
       │
       ▼
┌──────────────────┐
│  ChatInput       │  User interface component
│  Component       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  ChatContext     │  React Context (State Management)
│  sendMessage()   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  API Client      │  HTTP POST /api/chats/{id}/messages
│  (messagesApi)   │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  Backend API                                        │
│  POST /api/chats/{chat_id}/messages                │
│                                                     │
│  1. Save user message to MongoDB                   │
│  2. Return 201 Created immediately                 │
│  3. Trigger background task for AI response        │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  Background Task (Asynchronous)                     │
│                                                     │
│  1. AIService.generate_response()                   │
│     │                                               │
│     ├─► Search Engine (3-Layer RAG)               │
│     │   │                                           │
│     │   ├─► Layer 1: Process query, generate      │
│     │   │           embedding                      │
│     │   │                                           │
│     │   ├─► Layer 2: Vector search in Pinecone    │
│     │   │           (find relevant documents)      │
│     │   │                                           │
│     │   └─► Layer 3: Generate response using       │
│     │               Gemini AI + retrieved docs     │
│     │                                               │
│     └─► Save AI response to MongoDB                │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Frontend Polling│  Poll GET /api/chats/{id}/messages
│  (Every 2s)      │  until AI response appears
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Update UI       │  Display both user and AI messages
│  ChatContext     │
└──────────────────┘
```

---

## 🎨 Frontend Detailed Explanation

### What is the Frontend?

The frontend is the **user interface** that users interact with in their web browser. It's built with **Next.js 14** (a React framework) and provides a modern, responsive chat interface similar to popular AI chat applications like Google's Gemini.

### Frontend Architecture

```
frontend/
├── app/                          # Next.js App Router (routing)
│   ├── (auth)/                  # Authentication routes (currently disabled)
│   │   ├── login/page.tsx       # Login page (redirects to chat)
│   │   └── signup/page.tsx      # Signup page (redirects to chat)
│   ├── (chat)/                  # Chat routes
│   │   └── chat/page.tsx        # Main chat interface
│   ├── layout.tsx                # Root layout (wraps all pages)
│   ├── page.tsx                  # Home page (redirects to /chat)
│   └── globals.css               # Global styles and theme variables
│
├── components/                   # Reusable UI components
│   ├── chat/                     # Chat-specific components
│   │   ├── ChatHeader.tsx        # Top header with logo
│   │   ├── ChatSidebar.tsx       # Left sidebar (chat history)
│   │   ├── ChatMessage.tsx       # Individual message display
│   │   ├── ChatInput.tsx         # Message input field
│   │   ├── ChatSidebarSheet.tsx  # Mobile sidebar (drawer)
│   │   └── UserAvatarMenu.tsx    # Avatar dropdown menu
│   ├── auth/                     # Authentication components (unused)
│   └── ui/                       # Base UI components (shadcn/ui)
│       ├── button.tsx
│       ├── dropdown-menu.tsx
│       ├── input.tsx
│       └── ... (other UI primitives)
│
├── lib/                          # Core application logic
│   ├── contexts/                 # React Context (global state)
│   │   ├── ChatContext.tsx       # Chat state & API calls
│   │   ├── AuthContext.tsx       # Authentication state
│   │   └── ThemeContext.tsx      # Theme & mode state
│   ├── api/                      # API communication layer
│   │   ├── client.ts             # HTTP client (base)
│   │   ├── chats.ts              # Chat API methods
│   │   ├── messages.ts            # Message API methods
│   │   └── mock.ts                # Mock API (for testing)
│   ├── types/                    # TypeScript type definitions
│   │   ├── chat.ts               # Chat & Message types
│   │   ├── auth.ts               # Auth types
│   │   └── api.ts                # API response types
│   └── utils/                    # Utility functions
│       ├── cn.ts                 # Class name utility
│       └── constants.ts          # App constants
│
├── config/                       # Configuration files
│   └── api.ts                    # API configuration (URL, mock mode)
│
└── public/                       # Static assets
    └── logo.png                  # App logo
```

### Key Frontend Concepts Explained

#### 1. **React Components** (Building Blocks)

Components are reusable pieces of UI. Think of them like LEGO blocks:

- **ChatMessage**: Displays one message (user or AI)
- **ChatInput**: The text box where users type
- **ChatSidebar**: Shows list of previous chats
- **ChatHeader**: Top bar with logo

Each component is a self-contained piece that can be reused and combined.

#### 2. **React Context** (Global State Management)

Context is like a **shared storage** that any component can access. We have three contexts:

**ChatContext** - Manages all chat-related data:
```typescript
{
  chats: Chat[]              // List of all chats
  currentChat: Chat | null   // Currently selected chat
  messages: Message[]        // Messages in current chat
  sendMessage()              // Function to send a message
  createChat()               // Function to create new chat
  // ... other functions
}
```

**AuthContext** - Manages user authentication:
```typescript
{
  user: User | null          // Current user info
  isAuthenticated: boolean   // Is user logged in?
  login()                    // Login function
  logout()                   // Logout function
}
```

**ThemeContext** - Manages visual theme:
```typescript
{
  themeName: 'caffeine' | 'neo-brutalism'  // Which theme?
  themeMode: 'light' | 'dark'              // Light or dark?
  setTheme()                               // Change theme
  toggleMode()                             // Toggle light/dark
}
```

#### 3. **API Client** (Communication Layer)

The API client is like a **messenger** between the frontend and backend:

```typescript
// When user sends a message:
messagesApi.createMessage(chatId, "Hello", "user")
  ↓
// Makes HTTP POST request to:
// http://localhost:8000/api/chats/{chatId}/messages
  ↓
// Backend processes and responds
  ↓
// Frontend receives response and updates UI
```

#### 4. **State Flow** (How Data Moves)

```
User Action (types message)
    ↓
Component (ChatInput) calls sendMessage()
    ↓
Context (ChatContext) processes request
    ↓
API Client (messagesApi) sends HTTP request
    ↓
Backend API receives and processes
    ↓
Response comes back
    ↓
Context updates state
    ↓
React re-renders components
    ↓
UI updates (message appears)
```

#### 5. **Polling Mechanism** (Waiting for AI Response)

Since AI responses are generated asynchronously (in the background), the frontend uses **polling**:

```typescript
// After sending user message:
1. User message is saved immediately
2. Frontend starts polling (checking every 2 seconds):
   - GET /api/chats/{id}/messages
   - Check if AI response exists
   - If yes: stop polling, update UI
   - If no: wait 2 seconds, check again
3. Maximum 15 attempts (30 seconds total)
```

This ensures the UI stays responsive while waiting for the AI to generate a response.

#### 5. **Theming System** (Visual Customization)

The app supports multiple themes using CSS variables:

```css
/* Theme variables are defined in globals.css */
:root[data-theme="caffeine"] {
  --primary: oklch(0.5 0.2 250);
  --background: oklch(0.95 0.01 250);
  /* ... more colors */
}

:root[data-theme="neo-brutalism"] {
  --primary: oklch(0.4 0.25 120);
  --background: oklch(0.98 0.02 120);
  /* ... more colors */
}
```

The `ThemeContext` applies the theme by setting `data-theme` attribute on the HTML element.

### Frontend User Experience Flow

1. **User Opens App**
   - App loads, checks for existing chats
   - If no chat exists, creates a new one
   - Shows personalized greeting

2. **User Types Message**
   - Types in ChatInput component
   - Clicks send button
   - Message appears immediately in chat

3. **AI Response Generation**
   - Loading indicator appears
   - Frontend polls backend every 2 seconds
   - When AI response is ready, it appears in chat

4. **User Browses Chat History**
   - Clicks on a chat in sidebar
   - Messages for that chat load
   - Can continue conversation

5. **User Changes Theme**
   - Hovers over avatar
   - Opens dropdown menu
   - Selects theme or toggles light/dark mode
   - UI updates instantly

### Frontend Technologies Explained

- **Next.js 14**: React framework with built-in routing, server-side rendering, and optimizations
- **TypeScript**: Adds type safety to JavaScript (catches errors before runtime)
- **Tailwind CSS**: Utility-first CSS framework (rapid styling)
- **shadcn/ui**: Pre-built, accessible UI components
- **React Context API**: Built-in state management (no external library needed)
- **date-fns**: Date formatting library

---

## ⚙️ Backend Explanation

### What is the Backend?

The backend is the **server-side application** that handles:
- Storing and retrieving chat data
- Processing user messages
- Generating AI responses using the RAG system
- Managing database operations

### Backend Architecture

```
backend/
├── api/                          # Main API application
│   ├── main.py                   # FastAPI app entry point
│   ├── database.py               # MongoDB connection
│   ├── models.py                 # Data models (Pydantic)
│   ├── create_indexes.py         # Database index setup
│   ├── routes/                   # API endpoints
│   │   ├── chats.py              # Chat CRUD endpoints
│   │   └── messages.py           # Message CRUD endpoints
│   └── services/                 # Business logic
│       ├── chat_service.py       # Chat operations
│       ├── message_service.py    # Message operations
│       └── ai_service.py         # AI integration
│
├── search engine/                # RAG search engine
│   └── search_engine.py          # 3-layer search system
│
├── data-preprocessing/           # Data processing scripts
├── embdedding/                   # Embedding generation scripts
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── run_api.py                    # Server startup script
```

### Backend Components Explained

#### 1. **FastAPI Application** (`api/main.py`)

FastAPI is the web framework that creates the REST API:

```python
app = FastAPI(title="Fairly Chat API")

# Register routes
app.include_router(chats.router)      # /api/chats endpoints
app.include_router(messages.router)  # /api/chats/{id}/messages endpoints
```

#### 2. **Routes** (API Endpoints)

Routes define the URLs that the API responds to:

**Chat Routes** (`api/routes/chats.py`):
- `GET /api/chats` - Get all chats
- `GET /api/chats/{id}` - Get specific chat
- `POST /api/chats` - Create new chat
- `PATCH /api/chats/{id}` - Update chat
- `DELETE /api/chats/{id}` - Delete chat

**Message Routes** (`api/routes/messages.py`):
- `GET /api/chats/{id}/messages` - Get all messages
- `POST /api/chats/{id}/messages` - Create message (triggers AI response)
- `PATCH /api/chats/{id}/messages/{msg_id}` - Update message
- `DELETE /api/chats/{id}/messages/{msg_id}` - Delete message

#### 3. **Services** (Business Logic)

Services contain the actual logic for operations:

**ChatService** - Handles chat operations:
```python
def create_chat() -> Chat:
    # Create new chat document in MongoDB
    # Return chat object
```

**MessageService** - Handles message operations:
```python
def create_message(chat_id, content, role) -> Message:
    # Save message to MongoDB
    # Update chat metadata (lastMessage, messageCount)
    # Return message object
```

**AIService** - Handles AI response generation:
```python
def generate_response(user_message) -> str:
    # Call search engine
    # Get AI response
    # Return response text
```

#### 4. **3-Layer RAG Search Engine**

The search engine is the **brain** of the application. It has 3 layers:

**Layer 1: Query Processing & Vectorization**
```
User Query: "What are my rights as a domestic worker?"
    ↓
1. Detect jurisdiction (if needed)
2. Refine prompt for better search
3. Generate embedding vector (3072 dimensions)
    ↓
Output: Embedding vector + refined query
```

**Layer 2: Vector Similarity Search**
```
Embedding Vector
    ↓
Search in Pinecone (vector database)
    ↓
Find top 8 most similar document chunks
    ↓
Retrieve full text from MongoDB
    ↓
Output: Relevant document chunks
```

**Layer 3: Response Generation**
```
Original Query + Refined Query + Document Chunks
    ↓
Send to Google Gemini AI with context
    ↓
AI generates response based on retrieved documents
    ↓
Output: Human-readable answer
```

#### 5. **Asynchronous AI Processing**

To keep the API responsive, AI responses are generated in the background:

```python
@router.post("/{chat_id}/messages")
async def create_message(chat_id, request, background_tasks):
    # 1. Save user message immediately
    message = MessageService.create_message(...)
    
    # 2. Trigger AI generation in background (non-blocking)
    if request.role == "user":
        background_tasks.add_task(
            generate_and_save_ai_response,
            chat_id,
            request.content
        )
    
    # 3. Return immediately (don't wait for AI)
    return {"data": message}
```

This means:
- User message is saved instantly
- API responds immediately (no waiting)
- AI response is generated in the background
- Frontend polls to check when AI response is ready

### Backend Data Models

**Chat Model**:
```python
{
  "id": "chat_123",
  "title": "My Chat",
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z",
  "lastMessage": "What are my rights?",
  "lastMessageAt": "2024-01-01T00:00:00Z",
  "messageCount": 2
}
```

**Message Model**:
```python
{
  "id": "msg_456",
  "chatId": "chat_123",
  "content": "What are my rights?",
  "role": "user",  # or "assistant"
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Backend Technologies Explained

- **FastAPI**: Modern Python web framework (fast, type-safe, auto-docs)
- **MongoDB**: NoSQL database (stores chats and messages)
- **Pinecone**: Vector database (stores document embeddings for similarity search)
- **Google Gemini API**: AI model for generating embeddings and responses
- **Pydantic**: Data validation library (ensures data integrity)
- **Uvicorn**: ASGI server (runs the FastAPI app)

---

## 🔄 How Frontend and Backend Work Together

### Complete Request-Response Cycle

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Sends Message                                  │
└─────────────────────────────────────────────────────────────┘

User types "What are my rights?" and clicks send
    ↓
ChatInput component calls sendMessage()
    ↓
ChatContext.sendMessage() is invoked
    ↓
API Client makes HTTP POST request:
    POST http://localhost:8000/api/chats/chat_123/messages
    Body: {"content": "What are my rights?", "role": "user"}
    ↓
Backend receives request at messages.py route
    ↓
MessageService.create_message() saves to MongoDB
    ↓
Backend triggers background task for AI response
    ↓
Backend returns 201 Created with user message
    ↓
Frontend receives response, adds message to UI
    ↓
Frontend starts polling for AI response

┌─────────────────────────────────────────────────────────────┐
│ STEP 2: AI Response Generation (Background)                │
└─────────────────────────────────────────────────────────────┘

Background task runs:
    ↓
AIService.generate_response("What are my rights?")
    ↓
Search Engine processes:
    ├─ Layer 1: Generate embedding
    ├─ Layer 2: Search Pinecone for similar documents
    └─ Layer 3: Generate response using Gemini AI
    ↓
MessageService.create_message() saves AI response to MongoDB
    ↓
Chat metadata updated (lastMessage, messageCount)

┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Frontend Polling                                    │
└─────────────────────────────────────────────────────────────┘

Frontend polls every 2 seconds:
    GET http://localhost:8000/api/chats/chat_123/messages
    ↓
Backend returns all messages (including new AI response)
    ↓
Frontend detects new AI message
    ↓
Frontend stops polling
    ↓
Frontend updates UI to show AI response
    ↓
User sees complete conversation
```

### API Contract

All API responses follow this format:

```json
{
  "data": <actual_data>,
  "message": "optional success message",
  "error": "optional error message"
}
```

**Success Example**:
```json
{
  "data": {
    "id": "msg_123",
    "content": "What are my rights?",
    "role": "user",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Error Example**:
```json
{
  "error": "Chat not found",
  "status": 404
}
```

---

## 🛠️ Technology Stack

### Frontend Stack
| Technology | Purpose | Version |
|------------|---------|---------|
| **Next.js** | React framework with routing | 14.0.0 |
| **React** | UI library | 18.2.0 |
| **TypeScript** | Type-safe JavaScript | 5.0.0 |
| **Tailwind CSS** | Utility-first CSS framework | 3.3.0 |
| **shadcn/ui** | UI component library | Latest |
| **date-fns** | Date formatting | 2.30.0 |

### Backend Stack
| Technology | Purpose | Version |
|------------|---------|---------|
| **FastAPI** | Python web framework | 0.104.0 |
| **Uvicorn** | ASGI server | 0.24.0 |
| **Pydantic** | Data validation | 2.5.0 |
| **PyMongo** | MongoDB driver | 4.6.0 |
| **Pinecone** | Vector database client | 3.0.0 |
| **Google Generative AI** | Gemini API client | 0.3.0 |

### External Services
| Service | Purpose |
|---------|---------|
| **MongoDB Atlas** | Cloud database (stores chats, messages) |
| **Pinecone** | Vector database (stores document embeddings) |
| **Google Gemini API** | AI model (embeddings + text generation) |

---

## 📁 Project Structure

```
HACK-RUC/
├── frontend/                     # Next.js frontend application
│   ├── app/                      # Next.js App Router
│   ├── components/               # React components
│   ├── lib/                      # Core logic (contexts, API, types)
│   ├── config/                   # Configuration files
│   ├── public/                   # Static assets
│   └── package.json              # Frontend dependencies
│
├── backend/                      # FastAPI backend application
│   ├── api/                      # API application code
│   ├── search engine/            # RAG search engine
│   ├── data-preprocessing/       # Data processing scripts
│   ├── embdedding/               # Embedding generation scripts
│   ├── .env                      # Environment variables
│   └── requirements.txt          # Backend dependencies
│
├── Data/                         # Source data files
│
└── PROJECT_DOCUMENTATION.md      # This file
```

---

## 🚀 Setup Instructions

### Prerequisites
- **Node.js** 18+ and npm (for frontend)
- **Python** 3.9+ and pip (for backend)
- **MongoDB Atlas** account (cloud database)
- **Pinecone** account (vector database)
- **Google Gemini API** key

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Create environment file** (`.env.local`):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_USE_MOCK_API=false
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

5. **Open browser**:
   Navigate to `http://localhost:3000`

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (`.env` file already exists):
   ```env
   MONGODB_USERNAME=your_username
   MONGODB_PASSWORD=your_password
   MONGODB_CLUSTER=your_cluster.mongodb.net
   MONGODB_APP_NAME=Cluster1
   MONGODB_DATABASE=fairly
   MONGODB_COLLECTION=fairly_chunks
   
   GEMINI_API_KEY=your_gemini_key
   
   PINECONE_API_KEY=your_pinecone_key
   PINECONE_INDEX_NAME=domestic-worker-rights
   
   EMBEDDING_MODEL=gemini-embedding-exp-03-07
   EMBEDDING_DIMENSION=3072
   GEMINI_MODEL=gemini-2.0-flash-exp
   TOP_K_RESULTS=8
   SIMILARITY_THRESHOLD=0.65
   
   API_PORT=8000
   API_HOST=0.0.0.0
   CORS_ORIGINS=http://localhost:3000
   ```

5. **Create database indexes**:
   ```bash
   python api/create_indexes.py
   ```

6. **Start the server**:
   ```bash
   python run_api.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

7. **Verify API is running**:
   - Open `http://localhost:8000/docs` (Swagger UI)
   - Or `http://localhost:8000/health` (health check)

### Testing the Integration

1. **Start backend** (terminal 1):
   ```bash
   cd backend
   python run_api.py
   ```

2. **Start frontend** (terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the flow**:
   - Open `http://localhost:3000`
   - Type a message and send
   - Wait for AI response (may take 10-30 seconds)
   - Verify message appears in chat

### Troubleshooting

**Frontend Issues**:
- Clear `.next` folder and restart: `rm -rf .next && npm run dev`
- Check browser console for errors
- Verify API URL in `.env.local`

**Backend Issues**:
- Check MongoDB connection in `.env`
- Verify Pinecone API key and index name
- Check Gemini API key is valid
- Review server logs for errors

**API Connection Issues**:
- Ensure backend is running on port 8000
- Check CORS settings in `backend/api/main.py`
- Verify `NEXT_PUBLIC_API_URL` in frontend `.env.local`

---

## 📝 Key Concepts Summary

### For Non-Technical Audiences

**What is Fairly?**
- A chat application that helps domestic workers learn about their legal rights
- Uses AI to answer questions based on real legal documents
- Works like ChatGPT, but specialized for legal information

**How does it work?**
1. User asks a question
2. System searches through legal documents
3. AI generates an answer based on found documents
4. Answer is displayed to the user

**What makes it special?**
- Answers are based on verified legal documents (not just AI knowledge)
- Supports multiple jurisdictions (different states/cities)
- Saves conversation history
- Easy to use interface

### For Technical Audiences

**Architecture Highlights**:
- **Frontend**: Next.js 14 with App Router, React Context for state, TypeScript for type safety
- **Backend**: FastAPI REST API with async background tasks
- **RAG System**: 3-layer architecture (query processing → vector search → response generation)
- **Data Flow**: Synchronous user message save, asynchronous AI response generation with polling
- **State Management**: React Context API (no Redux needed)
- **Styling**: Tailwind CSS with CSS variables for theming

**Design Decisions**:
- **No authentication** (for MVP): Simplifies development, can be added later
- **Background tasks**: Keeps API responsive while AI generates responses
- **Polling mechanism**: Simple, reliable way to retrieve async AI responses
- **Local storage fallback**: App works even if API is temporarily unavailable
- **Component-based architecture**: Easy to modify and extend

---

## 🎓 Learning Resources

If you want to understand the technologies better:

- **Next.js**: https://nextjs.org/docs
- **React**: https://react.dev
- **FastAPI**: https://fastapi.tiangolo.com
- **RAG Systems**: https://www.pinecone.io/learn/retrieval-augmented-generation/
- **MongoDB**: https://www.mongodb.com/docs/
- **Pinecone**: https://docs.pinecone.io/

---

## 📞 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review server logs (backend terminal)
3. Check browser console (frontend)
4. Review API documentation at `http://localhost:8000/docs`

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Project**: Fairly - Domestic Worker Rights Chat Application

