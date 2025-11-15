# API Testing Guide - Fairly Backend

## 🚀 Quick Start Testing

### Step 1: Start the Server

```bash
cd backend
python run_api.py
```

You should see:
```
======================================================================
Starting Fairly Chat API Server
======================================================================
Host: 0.0.0.0
Port: 8000
CORS Origins: http://localhost:3000
======================================================================

API Documentation available at: http://localhost:8000/docs
======================================================================
```

### Step 2: Verify Server is Running

Open your browser and go to:
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

You should see `{"status": "healthy"}` for the health endpoint.

---

## 📋 Method 1: Swagger UI (Easiest - Recommended)

### Access Swagger UI

1. Open http://localhost:8000/docs in your browser
2. You'll see all 9 endpoints listed with their details
3. Click "Try it out" on any endpoint
4. Fill in the parameters/request body
5. Click "Execute"
6. See the response below

### Test Flow (Recommended Order)

#### 1. Create a Chat
- Endpoint: `POST /api/chats`
- Click "Try it out"
- Request body:
  ```json
  {
    "title": "Test Chat"
  }
  ```
- Click "Execute"
- **Expected**: Status 201, returns chat object with `id`, `title`, `createdAt`, etc.
- **Copy the `id`** from the response for next steps

#### 2. Get All Chats
- Endpoint: `GET /api/chats`
- Click "Try it out" → "Execute"
- **Expected**: Status 200, returns array with your created chat

#### 3. Get Specific Chat
- Endpoint: `GET /api/chats/{chat_id}`
- Click "Try it out"
- Paste the `chat_id` from step 1
- Click "Execute"
- **Expected**: Status 200, returns the specific chat

#### 4. Create a User Message
- Endpoint: `POST /api/chats/{chat_id}/messages`
- Click "Try it out"
- Paste the `chat_id`
- Request body:
  ```json
  {
    "content": "What are my rights as a domestic worker?",
    "role": "user"
  }
  ```
- Click "Execute"
- **Expected**: Status 201, returns user message
- **Note**: This will automatically trigger an AI response!

#### 5. Get Messages
- Endpoint: `GET /api/chats/{chat_id}/messages`
- Click "Try it out"
- Paste the `chat_id`
- Click "Execute"
- **Expected**: Status 200, returns array with both user and assistant messages

#### 6. Update Chat Title
- Endpoint: `PATCH /api/chats/{chat_id}`
- Click "Try it out"
- Paste the `chat_id`
- Request body:
  ```json
  {
    "title": "Updated Chat Title"
  }
  ```
- Click "Execute"
- **Expected**: Status 200, returns updated chat

#### 7. Update Message
- Endpoint: `PATCH /api/chats/{chat_id}/messages/{message_id}`
- Click "Try it out"
- Paste `chat_id` and `message_id` (from step 4)
- Request body:
  ```json
  {
    "content": "Updated message content"
  }
  ```
- Click "Execute"
- **Expected**: Status 200, returns updated message

#### 8. Delete Message
- Endpoint: `DELETE /api/chats/{chat_id}/messages/{message_id}`
- Click "Try it out"
- Paste `chat_id` and `message_id`
- Click "Execute"
- **Expected**: Status 200, returns `{"data": null}`

#### 9. Delete Chat
- Endpoint: `DELETE /api/chats/{chat_id}`
- Click "Try it out"
- Paste the `chat_id`
- Click "Execute"
- **Expected**: Status 200, returns `{"data": null}`

---

## 📋 Method 2: cURL Commands

### Prerequisites
Make sure the server is running on `http://localhost:8000`

### Test Script

Save this as `test_api.sh` (or run commands individually):

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api"

echo "🧪 Testing Fairly API"
echo "===================="

# 1. Health Check
echo -e "\n1. Health Check"
curl -s http://localhost:8000/health | python -m json.tool

# 2. Create Chat
echo -e "\n2. Creating Chat..."
CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/chats" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}')
echo "$CHAT_RESPONSE" | python -m json.tool

# Extract chat_id (requires jq or manual copy)
CHAT_ID=$(echo "$CHAT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
echo "Chat ID: $CHAT_ID"

# 3. Get All Chats
echo -e "\n3. Getting All Chats..."
curl -s "$BASE_URL/chats" | python -m json.tool

# 4. Get Specific Chat
echo -e "\n4. Getting Chat by ID..."
curl -s "$BASE_URL/chats/$CHAT_ID" | python -m json.tool

# 5. Create User Message
echo -e "\n5. Creating User Message..."
MESSAGE_RESPONSE=$(curl -s -X POST "$BASE_URL/chats/$CHAT_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "What are my rights?", "role": "user"}')
echo "$MESSAGE_RESPONSE" | python -m json.tool

# Wait a bit for AI response
echo -e "\n⏳ Waiting 3 seconds for AI response..."
sleep 3

# 6. Get Messages
echo -e "\n6. Getting Messages..."
curl -s "$BASE_URL/chats/$CHAT_ID/messages" | python -m json.tool

# 7. Update Chat
echo -e "\n7. Updating Chat..."
curl -s -X PATCH "$BASE_URL/chats/$CHAT_ID" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}' | python -m json.tool

echo -e "\n✅ Testing Complete!"
```

### Individual cURL Commands (Windows PowerShell)

```powershell
# 1. Health Check
curl http://localhost:8000/health

# 2. Create Chat
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/chats" -Method POST -ContentType "application/json" -Body '{"title": "Test Chat"}'
$chatId = $response.data.id
Write-Host "Chat ID: $chatId"

# 3. Get All Chats
Invoke-RestMethod -Uri "http://localhost:8000/api/chats" -Method GET

# 4. Get Specific Chat
Invoke-RestMethod -Uri "http://localhost:8000/api/chats/$chatId" -Method GET

# 5. Create User Message
Invoke-RestMethod -Uri "http://localhost:8000/api/chats/$chatId/messages" -Method POST -ContentType "application/json" -Body '{"content": "What are my rights?", "role": "user"}'

# Wait for AI response
Start-Sleep -Seconds 3

# 6. Get Messages
Invoke-RestMethod -Uri "http://localhost:8000/api/chats/$chatId/messages" -Method GET

# 7. Update Chat
Invoke-RestMethod -Uri "http://localhost:8000/api/chats/$chatId" -Method PATCH -ContentType "application/json" -Body '{"title": "Updated Title"}'

# 8. Delete Chat
Invoke-RestMethod -Uri "http://localhost:8000/api/chats/$chatId" -Method DELETE
```

---

## 📋 Method 3: Python Test Script

Create `test_api.py`:

```python
#!/usr/bin/env python3
"""
Test script for Fairly API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_api():
    print("🧪 Testing Fairly API")
    print("=" * 50)
    
    # 1. Health Check
    print("\n1. Health Check")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 2. Create Chat
    print("\n2. Creating Chat...")
    response = requests.post(
        f"{BASE_URL}/chats",
        json={"title": "Test Chat"}
    )
    print(f"Status: {response.status_code}")
    chat_data = response.json()
    print(f"Response: {json.dumps(chat_data, indent=2)}")
    chat_id = chat_data["data"]["id"]
    print(f"Chat ID: {chat_id}")
    
    # 3. Get All Chats
    print("\n3. Getting All Chats...")
    response = requests.get(f"{BASE_URL}/chats")
    print(f"Status: {response.status_code}")
    print(f"Total chats: {len(response.json()['data'])}")
    
    # 4. Get Specific Chat
    print("\n4. Getting Chat by ID...")
    response = requests.get(f"{BASE_URL}/chats/{chat_id}")
    print(f"Status: {response.status_code}")
    print(f"Chat title: {response.json()['data']['title']}")
    
    # 5. Create User Message
    print("\n5. Creating User Message...")
    response = requests.post(
        f"{BASE_URL}/chats/{chat_id}/messages",
        json={"content": "What are my rights as a domestic worker?", "role": "user"}
    )
    print(f"Status: {response.status_code}")
    message_data = response.json()
    print(f"User message created: {message_data['data']['content'][:50]}...")
    
    # Wait for AI response
    print("\n⏳ Waiting 5 seconds for AI response...")
    time.sleep(5)
    
    # 6. Get Messages
    print("\n6. Getting Messages...")
    response = requests.get(f"{BASE_URL}/chats/{chat_id}/messages")
    print(f"Status: {response.status_code}")
    messages = response.json()["data"]
    print(f"Total messages: {len(messages)}")
    for i, msg in enumerate(messages, 1):
        print(f"  {i}. [{msg['role']}]: {msg['content'][:60]}...")
    
    # 7. Update Chat
    print("\n7. Updating Chat...")
    response = requests.patch(
        f"{BASE_URL}/chats/{chat_id}",
        json={"title": "Updated Chat Title"}
    )
    print(f"Status: {response.status_code}")
    print(f"New title: {response.json()['data']['title']}")
    
    # 8. Update Message
    if messages:
        print("\n8. Updating Message...")
        message_id = messages[0]["id"]
        response = requests.patch(
            f"{BASE_URL}/chats/{chat_id}/messages/{message_id}",
            json={"content": "Updated message content"}
        )
        print(f"Status: {response.status_code}")
        print(f"Updated content: {response.json()['data']['content']}")
    
    # 9. Delete Chat
    print("\n9. Deleting Chat...")
    response = requests.delete(f"{BASE_URL}/chats/{chat_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
```

Run it:
```bash
cd backend
pip install requests  # if not already installed
python test_api.py
```

---

## 📋 Method 4: Postman/Insomnia

### Import Collection

1. **Create New Collection** in Postman/Insomnia
2. **Set Base URL**: `http://localhost:8000/api`
3. **Add Requests**:

#### Request 1: Health Check
- Method: `GET`
- URL: `http://localhost:8000/health`

#### Request 2: Create Chat
- Method: `POST`
- URL: `{{base_url}}/chats`
- Body (JSON):
  ```json
  {
    "title": "Test Chat"
  }
  ```

#### Request 3: Get All Chats
- Method: `GET`
- URL: `{{base_url}}/chats`

#### Request 4: Get Chat by ID
- Method: `GET`
- URL: `{{base_url}}/chats/{{chat_id}}`
- (Set `chat_id` variable from Request 2 response)

#### Request 5: Create Message
- Method: `POST`
- URL: `{{base_url}}/chats/{{chat_id}}/messages`
- Body (JSON):
  ```json
  {
    "content": "What are my rights?",
    "role": "user"
  }
  ```

#### Request 6: Get Messages
- Method: `GET`
- URL: `{{base_url}}/chats/{{chat_id}}/messages`

#### Request 7: Update Chat
- Method: `PATCH`
- URL: `{{base_url}}/chats/{{chat_id}}`
- Body (JSON):
  ```json
  {
    "title": "Updated Title"
  }
  ```

#### Request 8: Update Message
- Method: `PATCH`
- URL: `{{base_url}}/chats/{{chat_id}}/messages/{{message_id}}`
- Body (JSON):
  ```json
  {
    "content": "Updated content"
  }
  ```

#### Request 9: Delete Message
- Method: `DELETE`
- URL: `{{base_url}}/chats/{{chat_id}}/messages/{{message_id}}`

#### Request 10: Delete Chat
- Method: `DELETE`
- URL: `{{base_url}}/chats/{{chat_id}}`

---

## ✅ Testing Checklist

### Basic Functionality
- [ ] Server starts without errors
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] Swagger UI loads at `/docs`
- [ ] Can create a chat
- [ ] Can get all chats
- [ ] Can get specific chat by ID
- [ ] Can create a user message
- [ ] AI response is automatically generated
- [ ] Can get messages for a chat
- [ ] Can update chat title
- [ ] Can update message content
- [ ] Can delete a message
- [ ] Can delete a chat

### Data Validation
- [ ] Creating chat without title generates default title
- [ ] Invalid chat ID returns 404
- [ ] Invalid message ID returns 404
- [ ] Invalid role (not "user" or "assistant") returns 400
- [ ] Empty message content returns 400
- [ ] Dates are in ISO 8601 format
- [ ] Response format matches spec: `{ "data": ..., "message": ..., "error": ... }`

### AI Integration
- [ ] User message triggers AI response
- [ ] AI response is saved as assistant message
- [ ] Chat metadata updates (lastMessage, lastMessageAt, messageCount)
- [ ] AI responses are relevant to the query

### Error Handling
- [ ] 404 errors return proper error message
- [ ] 400 errors return validation messages
- [ ] 500 errors are handled gracefully
- [ ] CORS headers are present

---

## 🐛 Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check `.env` file exists and has correct values

### Import errors
- Make sure you're running from the `backend` directory
- Verify Python path includes backend directory

### MongoDB connection errors
- Verify MongoDB credentials in `.env`
- Check MongoDB Atlas IP whitelist
- Test connection: `python -c "from api.database import Database; Database.connect()"`

### AI responses not working
- Verify Gemini API key in `.env`
- Check Pinecone API key and index name
- Look for error messages in server logs
- Test search engine directly: `python "search engine/search_engine.py"`

### CORS errors
- Verify `CORS_ORIGINS` in `.env` includes your frontend URL
- Check browser console for specific CORS errors

---

## 🎯 Quick Test Command

Run this one-liner to test basic functionality:

```bash
# Create chat, send message, get messages
curl -X POST http://localhost:8000/api/chats -H "Content-Type: application/json" -d '{"title":"Quick Test"}' | python -m json.tool
```

---

## 📊 Expected Response Times

- Health check: < 100ms
- Create chat: < 200ms
- Get chats: < 300ms
- Create message: < 500ms (user) + 2-5s (AI response)
- Get messages: < 300ms
- Update/Delete: < 200ms

---

**Happy Testing! 🚀**

