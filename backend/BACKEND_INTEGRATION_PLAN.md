# Backend API Specification - Fairly Chat Application

## Overview

This document specifies the backend API requirements for the **Fairly** chat application. The frontend is a Next.js application that currently uses a mock API and needs to be connected to a real backend.

**Important Notes:**
- **No Authentication Required**: The app works without authentication. All endpoints should be publicly accessible.
- **Core Features Only**: Focus on chat and message management. Authentication can be added later.
- **Technology Agnostic**: Use any backend technology (Node.js, Python, Go, Java, etc.) - just match the API contract.

---

## API Contract Summary

### Base URL
```
http://localhost:8000/api
```
(Or any URL you prefer - frontend will be configured to match)

### Response Format
All responses must follow this structure:
```json
{
  "data": <actual_data>,
  "message": "optional success message",
  "error": "optional error message"
}
```

### Error Format
Errors should return appropriate HTTP status codes with this format:
```json
{
  "error": "Error message",
  "message": "Optional detailed message",
  "status": 400
}
```

### Date Format
All dates must be sent as **ISO 8601 strings** (e.g., `"2024-01-15T10:30:00.000Z"`). The frontend will automatically convert them to Date objects.

### HTTP Status Codes
- `200`: Success
- `201`: Created (for POST requests)
- `400`: Bad Request (validation errors)
- `404`: Not Found
- `500`: Internal Server Error

---

## Data Models

### Chat Model
```typescript
interface Chat {
  id: string                    // Unique identifier (UUID or string)
  title: string                 // Chat title (e.g., "New Chat 1")
  createdAt: string             // ISO 8601 date string
  updatedAt: string             // ISO 8601 date string
  lastMessage?: string          // Optional: First 100 chars of last message
  lastMessageAt?: string        // Optional: ISO 8601 date string
  messageCount: number          // Number of messages in this chat
  userId: string               // User identifier (can be "anonymous" for now)
}
```

### Message Model
```typescript
interface Message {
  id: string                    // Unique identifier (UUID or string)
  content: string               // Message content/text
  role: 'user' | 'assistant'   // Message role
  timestamp: string             // ISO 8601 date string
  chatId: string                // ID of the chat this message belongs to
}
```

---

## API Endpoints

### 1. Chat Endpoints

#### GET /api/chats
**Description**: Get all chats

**Request**: 
- Method: `GET`
- Headers: `Content-Type: application/json`
- Body: None

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "chat-123",
      "title": "New Chat 1",
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-15T10:35:00.000Z",
      "lastMessage": "Hello, how can I help you?",
      "lastMessageAt": "2024-01-15T10:35:00.000Z",
      "messageCount": 5,
      "userId": "anonymous"
    }
  ]
}
```

**Error Responses**:
- `500`: Internal Server Error

---

#### GET /api/chats/:id
**Description**: Get a specific chat by ID

**Request**:
- Method: `GET`
- Path Parameters: `id` (string) - Chat ID
- Headers: `Content-Type: application/json`
- Body: None

**Response** (200 OK):
```json
{
  "data": {
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
```

**Error Responses**:
- `404`: Chat not found
- `500`: Internal Server Error

---

#### POST /api/chats
**Description**: Create a new chat

**Request**:
- Method: `POST`
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "title": "New Chat 1"  // Optional: If not provided, backend can generate a default title
}
```

**Response** (201 Created):
```json
{
  "data": {
    "id": "chat-123",
    "title": "New Chat 1",
    "createdAt": "2024-01-15T10:30:00.000Z",
    "updatedAt": "2024-01-15T10:30:00.000Z",
    "messageCount": 0,
    "userId": "anonymous"
  }
}
```

**Error Responses**:
- `400`: Invalid request (e.g., invalid title format)
- `500`: Internal Server Error

**Notes**:
- Backend should generate a unique ID for the chat
- Set `createdAt` and `updatedAt` to current timestamp
- Set `messageCount` to 0
- `userId` can be "anonymous" for now (or any default value)

---

#### PATCH /api/chats/:id
**Description**: Update a chat (primarily for updating title)

**Request**:
- Method: `PATCH`
- Path Parameters: `id` (string) - Chat ID
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "title": "Updated Chat Title"  // Optional: Only fields to update
}
```

**Response** (200 OK):
```json
{
  "data": {
    "id": "chat-123",
    "title": "Updated Chat Title",
    "createdAt": "2024-01-15T10:30:00.000Z",
    "updatedAt": "2024-01-15T10:40:00.000Z",
    "lastMessage": "Hello, how can I help you?",
    "lastMessageAt": "2024-01-15T10:35:00.000Z",
    "messageCount": 5,
    "userId": "anonymous"
  }
}
```

**Error Responses**:
- `400`: Invalid request
- `404`: Chat not found
- `500`: Internal Server Error

**Notes**:
- Update `updatedAt` to current timestamp
- Only update fields provided in request body

---

#### DELETE /api/chats/:id
**Description**: Delete a chat and all its messages

**Request**:
- Method: `DELETE`
- Path Parameters: `id` (string) - Chat ID
- Headers: `Content-Type: application/json`
- Body: None

**Response** (200 OK):
```json
{
  "data": null
}
```

**Error Responses**:
- `404`: Chat not found
- `500`: Internal Server Error

**Notes**:
- Deleting a chat should also delete all associated messages
- Return success even if chat doesn't exist (idempotent)

---

### 2. Message Endpoints

#### GET /api/chats/:chatId/messages
**Description**: Get all messages for a specific chat

**Request**:
- Method: `GET`
- Path Parameters: `chatId` (string) - Chat ID
- Headers: `Content-Type: application/json`
- Body: None

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "msg-1",
      "content": "Hello, how can I help you?",
      "role": "user",
      "timestamp": "2024-01-15T10:30:00.000Z",
      "chatId": "chat-123"
    },
    {
      "id": "msg-2",
      "content": "I can help you with various tasks!",
      "role": "assistant",
      "timestamp": "2024-01-15T10:30:05.000Z",
      "chatId": "chat-123"
    }
  ]
}
```

**Error Responses**:
- `404`: Chat not found
- `500`: Internal Server Error

**Notes**:
- Messages should be returned in chronological order (oldest first)
- If chat has no messages, return empty array: `{ "data": [] }`

---

#### POST /api/chats/:chatId/messages
**Description**: Create a new message in a chat

**Request**:
- Method: `POST`
- Path Parameters: `chatId` (string) - Chat ID
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "content": "Hello, how can I help you?",
  "role": "user"  // Must be either "user" or "assistant"
}
```

**Response** (201 Created):
```json
{
  "data": {
    "id": "msg-1",
    "content": "Hello, how can I help you?",
    "role": "user",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "chatId": "chat-123"
  }
}
```

**Error Responses**:
- `400`: Invalid request (e.g., invalid role, empty content)
- `404`: Chat not found
- `500`: Internal Server Error

**Notes**:
- Backend should generate a unique ID for the message
- Set `timestamp` to current timestamp
- Set `chatId` from path parameter
- After creating a message, backend should update the chat's:
  - `lastMessage`: First 100 characters of the message content
  - `lastMessageAt`: Current timestamp
  - `updatedAt`: Current timestamp
  - `messageCount`: Increment by 1

---

#### PATCH /api/chats/:chatId/messages/:messageId
**Description**: Update a message (primarily for editing content)

**Request**:
- Method: `PATCH`
- Path Parameters: 
  - `chatId` (string) - Chat ID
  - `messageId` (string) - Message ID
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "content": "Updated message content"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "id": "msg-1",
    "content": "Updated message content",
    "role": "user",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "chatId": "chat-123"
  }
}
```

**Error Responses**:
- `400`: Invalid request
- `404`: Message not found
- `500`: Internal Server Error

**Notes**:
- Only update fields provided in request body
- If message is the last message in chat, update chat's `lastMessage` field

---

#### DELETE /api/chats/:chatId/messages/:messageId
**Description**: Delete a message

**Request**:
- Method: `DELETE`
- Path Parameters:
  - `chatId` (string) - Chat ID
  - `messageId` (string) - Message ID
- Headers: `Content-Type: application/json`
- Body: None

**Response** (200 OK):
```json
{
  "data": null
}
```

**Error Responses**:
- `404`: Message not found
- `500`: Internal Server Error

**Notes**:
- If deleted message was the last message, update chat's `lastMessage` and `lastMessageAt` to previous message
- Decrement chat's `messageCount` by 1
- Update chat's `updatedAt` to current timestamp

---

## Implementation Guidelines

### Technology Stack
Use **any backend technology** you prefer:
- **Node.js**: Express, Fastify, NestJS
- **Python**: Flask, FastAPI, Django
- **Go**: Gin, Echo, Fiber
- **Java**: Spring Boot
- **Ruby**: Rails
- **PHP**: Laravel
- Or any other framework

### Database
Use **any database** you prefer:
- PostgreSQL
- MySQL
- MongoDB
- SQLite (for development)
- Or any other database

### Key Implementation Requirements

1. **CORS Configuration**
   - Enable CORS for frontend origin
   - For development: Allow `http://localhost:3000`
   - Include headers: `Content-Type`, `Accept`

2. **ID Generation**
   - Generate unique IDs for chats and messages
   - Can use UUIDs, nanoid, or any unique string generator
   - IDs should be URL-safe strings

3. **Data Validation**
   - Validate request bodies
   - Ensure required fields are present
   - Validate data types (string, number, etc.)
   - Validate `role` is either "user" or "assistant"

4. **Error Handling**
   - Return appropriate HTTP status codes
   - Return error messages in specified format
   - Log errors server-side for debugging

5. **Date Handling**
   - Store dates in your database format
   - Convert to ISO 8601 strings when sending to frontend
   - Use UTC timezone

6. **Chat Updates**
   - When a message is created/updated/deleted, update the chat's metadata:
     - `lastMessage`: First 100 characters of most recent message
     - `lastMessageAt`: Timestamp of most recent message
     - `updatedAt`: Current timestamp
     - `messageCount`: Total count of messages

### Example Backend Structure

```
backend/
├── routes/
│   ├── chats.js          # Chat endpoints
│   └── messages.js       # Message endpoints
├── models/
│   ├── Chat.js           # Chat model/schema
│   └── Message.js        # Message model/schema
├── controllers/
│   ├── chatController.js
│   └── messageController.js
├── middleware/
│   ├── errorHandler.js
│   └── cors.js
└── server.js             # Main server file
```

---

## Testing the API

### Using cURL

#### Create a Chat
```bash
curl -X POST http://localhost:8000/api/chats \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}'
```

#### Get All Chats
```bash
curl -X GET http://localhost:8000/api/chats \
  -H "Content-Type: application/json"
```

#### Create a Message
```bash
curl -X POST http://localhost:8000/api/chats/chat-123/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!", "role": "user"}'
```

#### Get Messages
```bash
curl -X GET http://localhost:8000/api/chats/chat-123/messages \
  -H "Content-Type: application/json"
```

### Using Postman/Insomnia

Import these endpoints:
- `POST /api/chats` - Create chat
- `GET /api/chats` - Get all chats
- `GET /api/chats/:id` - Get chat
- `PATCH /api/chats/:id` - Update chat
- `DELETE /api/chats/:id` - Delete chat
- `GET /api/chats/:chatId/messages` - Get messages
- `POST /api/chats/:chatId/messages` - Create message
- `PATCH /api/chats/:chatId/messages/:messageId` - Update message
- `DELETE /api/chats/:chatId/messages/:messageId` - Delete message

---

## Frontend Integration

### Environment Configuration

Once your backend is ready, update the frontend `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK_API=false
```

### Frontend Code Structure

The frontend already has the service layer set up:
- `frontend/lib/api/chats.ts` - Chat API service
- `frontend/lib/api/messages.ts` - Message API service
- `frontend/lib/api/client.ts` - HTTP client
- `frontend/config/api.ts` - API configuration

**No frontend code changes needed** - just ensure your backend matches this API contract.

---

## Common Issues & Solutions

### 1. CORS Errors
**Symptom**: `Access-Control-Allow-Origin` errors in browser console

**Solution**: 
- Enable CORS middleware in your backend
- Allow origin: `http://localhost:3000` (or your frontend URL)
- Include headers: `Content-Type`, `Accept`, `Authorization`

### 2. Date Format Issues
**Symptom**: Frontend shows "Invalid Date"

**Solution**:
- Ensure all dates are sent as ISO 8601 strings
- Format: `"2024-01-15T10:30:00.000Z"`
- Use UTC timezone

### 3. Missing Fields
**Symptom**: Frontend errors about missing properties

**Solution**:
- Ensure all required fields are returned in responses
- Check data models match exactly
- Verify nested objects are included

### 4. 404 Errors
**Symptom**: Endpoints return 404

**Solution**:
- Verify route paths match exactly (case-sensitive)
- Check base URL is correct
- Ensure server is running on correct port

---

## Quick Start Checklist

For backend developers using this spec:

- [ ] Choose your technology stack (Node.js, Python, Go, etc.)
- [ ] Set up project structure
- [ ] Create database schema/models for Chat and Message
- [ ] Implement GET /api/chats endpoint
- [ ] Implement POST /api/chats endpoint
- [ ] Implement GET /api/chats/:id endpoint
- [ ] Implement PATCH /api/chats/:id endpoint
- [ ] Implement DELETE /api/chats/:id endpoint
- [ ] Implement GET /api/chats/:chatId/messages endpoint
- [ ] Implement POST /api/chats/:chatId/messages endpoint
- [ ] Implement PATCH /api/chats/:chatId/messages/:messageId endpoint
- [ ] Implement DELETE /api/chats/:chatId/messages/:messageId endpoint
- [ ] Configure CORS
- [ ] Test all endpoints with cURL/Postman
- [ ] Verify date formats are ISO 8601
- [ ] Verify response format matches spec
- [ ] Update frontend `.env.local` with backend URL
- [ ] Test frontend integration

---

## Future Enhancements (Not Required Now)

These features can be added later:
- Authentication & Authorization
- User management
- Rate limiting
- Pagination for large datasets
- Search functionality
- Real-time updates (WebSockets)
- File uploads
- Message streaming

---

## Support

If you have questions about the API contract:
1. Check the data models section for expected structure
2. Review the example responses in each endpoint
3. Test with the provided cURL commands
4. Verify your responses match the TypeScript interfaces

**Remember**: The frontend is already built and ready. Your job is to create a backend that matches this API contract. No authentication needed - keep it simple and focus on core chat functionality.

