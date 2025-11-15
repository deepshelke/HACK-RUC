# Frontend-Backend Integration Plan

## Overview
Integrate the Next.js frontend with the FastAPI backend to enable real-time chat with AI-powered responses.

## Current State

### ✅ Frontend Ready
- API client configured
- Service layer implemented (chatsApi, messagesApi)
- ChatContext supports both mock and real API
- Mock API toggle via `USE_MOCK_API` flag

### ✅ Backend Ready
- FastAPI server running on port 8000
- All 9 endpoints implemented
- AI responses generated in background
- CORS configured for frontend

## Integration Steps

### Phase 1: Environment Configuration (5 min)
1. Create `.env.local` file
2. Set `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Set `NEXT_PUBLIC_USE_MOCK_API=false`

### Phase 2: Update ChatContext (15 min)
1. Remove simulated assistant response
2. Use real API for message creation
3. Implement polling for AI responses (since they're generated in background)
4. Handle real API responses properly

### Phase 3: Error Handling (10 min)
1. Add better error messages
2. Handle network errors gracefully
3. Show loading states during AI generation

### Phase 4: Testing (10 min)
1. Test chat creation
2. Test message sending
3. Verify AI responses appear
4. Test error scenarios

## Key Changes Needed

### 1. Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK_API=false
```

### 2. ChatContext Updates
- Remove simulated assistant response (lines 314-334)
- Use real API call for user messages
- Implement polling mechanism for AI responses
- Handle background AI generation

### 3. AI Response Polling
Since AI responses are generated in background, we need to:
- Poll for new messages after sending user message
- Show loading indicator while waiting
- Stop polling when AI response arrives

## Implementation Strategy

1. **Immediate Response**: User message appears instantly
2. **Background AI**: AI response generated on backend
3. **Polling**: Frontend polls for new messages every 2-3 seconds
4. **Update UI**: When AI response appears, update messages list
5. **Stop Polling**: After AI response or timeout (30 seconds)

## Testing Checklist

- [ ] Frontend connects to backend
- [ ] Chat creation works
- [ ] User messages are sent and saved
- [ ] AI responses appear after generation
- [ ] Error handling works
- [ ] Loading states display correctly
- [ ] Polling stops when response arrives

