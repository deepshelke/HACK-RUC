# Implementation Plan - HACK-RUC Frontend

## Overview
This document outlines the plan for restructuring and enhancing the HACK-RUC frontend with improved architecture, authentication, previous chats, and shadcn/ui integration.

## Goals
1. **Maintainable Architecture**: Create a scalable structure that's easy to modify and extend
2. **API Integration Ready**: Design patterns that make backend integration seamless
3. **Optional Authentication**: Users can use chat without authentication; auth is prompted only when needed
4. **Local Storage Support**: Unauthenticated users can use chat with local storage persistence
5. **Previous Chats**: Sidebar showing chat history with ability to switch between chats
6. **shadcn/ui Integration**: Use shadcn/ui components for consistent, accessible UI

---

## Phase 1: Architecture Restructuring

### 1.1 Folder Structure
```
frontend/
├── app/                    # Next.js app router
│   ├── (auth)/            # Auth routes (login, signup)
│   │   ├── login/
│   │   └── signup/
│   ├── (chat)/            # Protected chat routes
│   │   ├── chat/
│   │   │   └── [chatId]/
│   │   └── layout.tsx
│   ├── layout.tsx
│   └── page.tsx           # Landing/redirect
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── auth/              # Auth components
│   ├── chat/              # Chat-specific components
│   └── layout/            # Layout components
├── lib/
│   ├── api/               # API service layer
│   │   ├── auth.ts
│   │   ├── chats.ts
│   │   └── messages.ts
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useChats.ts
│   │   └── useMessages.ts
│   ├── contexts/          # React contexts
│   │   ├── AuthContext.tsx
│   │   └── ChatContext.tsx
│   ├── utils/             # Utility functions
│   │   ├── cn.ts
│   │   └── constants.ts
│   └── types/             # TypeScript types
│       ├── auth.ts
│       ├── chat.ts
│       └── api.ts
└── config/                # Configuration files
    └── api.ts             # API endpoints config
```

### 1.2 Key Architectural Decisions

**Service Layer Pattern**
- All API calls abstracted into service functions
- Easy to swap mock data with real API calls
- Centralized error handling

**Context API for State Management**
- `AuthContext`: User authentication state
- `ChatContext`: Current chat and messages state
- Makes state accessible across components

**Custom Hooks**
- Encapsulate business logic
- Reusable across components
- Easy to test and maintain

**Type Safety**
- Centralized type definitions
- Shared between frontend and (potentially) backend
- Prevents type mismatches

---

## Phase 2: shadcn/ui Setup

### 2.1 Installation
- Initialize shadcn/ui with `npx shadcn-ui@latest init`
- Configure components.json
- Set up proper path aliases

### 2.2 Components to Install
- **Button**: For all interactive buttons
- **Input**: Form inputs
- **Card**: Container components
- **Dialog**: Modals (auth, settings)
- **Sheet**: Sidebar for previous chats
- **Avatar**: User profile images
- **Badge**: Status indicators
- **Separator**: Visual dividers
- **ScrollArea**: Custom scrollbars
- **Skeleton**: Loading states
- **Toast**: Notifications

### 2.3 Theme Configuration
- Customize shadcn theme to match Gemini-inspired design
- Maintain gradient accents (blue to purple)
- Ensure dark mode compatibility

---

## Phase 3: Authentication Implementation (Optional)

### 3.1 Authentication Strategy
- **No Authentication Required**: Users can access and use the chat interface without signing in
- **Local Storage**: Unauthenticated users' chats are stored in browser local storage
- **Optional Sign-in**: Authentication is prompted only when users want to:
  - Sync chats across devices
  - Access cloud-saved chats
  - Use premium features (future)

### 3.2 Auth Pages
- **Login Page** (`/login`)
  - Email/password form
  - "Forgot password" link
  - "Sign up" link
  - Social auth buttons (optional, for future)

- **Signup Page** (`/signup`)
  - Email, password, confirm password
  - Terms acceptance
  - "Already have account" link

### 3.3 Auth Components
- `LoginForm`: Login form component
- `SignupForm`: Signup form component
- `AuthPrompt`: Modal/dialog for prompting authentication when needed
- `AuthLayout`: Shared layout for auth pages

### 3.4 Auth Context
- `AuthContext` provides:
  - `user`: Current user object (null if not authenticated)
  - `isAuthenticated`: Boolean
  - `isLoading`: Loading state
  - `login(email, password)`: Login function
  - `signup(email, password, name)`: Signup function
  - `logout()`: Logout function
  - `refreshToken()`: Token refresh (if needed)

### 3.4 API Integration Points
```typescript
// lib/api/auth.ts
- login(email, password) -> POST /api/auth/login
- signup(email, password, name) -> POST /api/auth/signup
- logout() -> POST /api/auth/logout
- getCurrentUser() -> GET /api/auth/me
- refreshToken() -> POST /api/auth/refresh
```

---

## Phase 4: Previous Chats Implementation

### 4.1 Chat Sidebar Component
- **Location**: Left side of chat interface (sheet on mobile)
- **Features**:
  - List of previous chats (from API if authenticated, local storage if not)
  - Search/filter chats (future)
  - Create new chat button
  - Delete chat option
  - Chat preview (last message, timestamp)
  - Active chat highlighting
  - Auth prompt for unauthenticated users

### 4.2 Chat Management
- **Chat Model**:
  ```typescript
  interface Chat {
    id: string
    title: string
    createdAt: Date
    updatedAt: Date
    lastMessage?: string
    lastMessageAt?: Date
    messageCount: number
    userId: string // 'anonymous' for unauthenticated users
  }
  ```

### 4.3 Chat Context (Dual Mode)
- `ChatContext` provides:
  - `chats`: Array of all chats (from API or local storage)
  - `currentChat`: Currently active chat
  - `createChat()`: Create new chat (local or API)
  - `selectChat(chatId)`: Switch to chat
  - `deleteChat(chatId)`: Delete chat
  - `updateChatTitle(chatId, title)`: Rename chat
  - Works seamlessly for both authenticated and unauthenticated users
  - Automatically syncs with API when user authenticates

### 4.4 API Integration Points
```typescript
// lib/api/chats.ts
- getChats() -> GET /api/chats
- getChat(chatId) -> GET /api/chats/:id
- createChat() -> POST /api/chats
- updateChat(chatId, data) -> PATCH /api/chats/:id
- deleteChat(chatId) -> DELETE /api/chats/:id
```

---

## Phase 5: Component Refactoring

### 5.1 Chat Components (using shadcn)
- **ChatMessage**: Use Card component, improve styling
- **ChatInput**: Use Input component, add file upload (future)
- **ChatHeader**: Use Avatar, Button, DropdownMenu
- **ChatSidebar**: Use Sheet, ScrollArea, Button

### 5.2 Layout Components
- **MainLayout**: Wrapper with sidebar and main content
- **AuthLayout**: Centered layout for auth pages
- **Header**: Top navigation bar

### 5.3 UI Improvements
- Better loading states with Skeleton
- Toast notifications for actions
- Smooth transitions and animations
- Responsive design (mobile-friendly)

---

## Phase 6: API Service Layer

### 6.1 API Client Setup
- Base API client with interceptors
- Request/response transformers
- Error handling
- Token management

### 6.2 Service Modules
- **auth.ts**: Authentication endpoints
- **chats.ts**: Chat management endpoints
- **messages.ts**: Message CRUD endpoints

### 6.3 Mock Data (Development)
- Mock API responses for development
- Easy to toggle between mock and real API
- Environment-based configuration

---

## Implementation Order

1. ✅ **Setup shadcn/ui** (Foundation)
2. ✅ **Restructure folders** (Architecture)
3. ✅ **Create types and interfaces** (Type safety)
4. ✅ **Build API service layer** (Backend integration)
5. ✅ **Implement AuthContext** (State management)
6. ✅ **Create auth pages** (UI)
7. ✅ **Implement ChatContext** (State management)
8. ✅ **Build chat sidebar** (UI)
9. ✅ **Refactor chat components** (UI improvements)
10. ✅ **Add routing and protection** (Navigation)
11. ✅ **Testing and polish** (Quality)

---

## API Integration Strategy

### Development Mode
- Use mock data and services
- Simulate API delays
- Test error scenarios

### Production Mode
- Switch to real API endpoints
- Configure base URL from environment variables
- Handle authentication tokens
- Implement retry logic

### Configuration
```typescript
// config/api.ts
export const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  // ... other config
}
```

---

## Future Enhancements (Out of Scope for Now)
- Real-time messaging (WebSockets)
- File uploads
- Markdown rendering in messages
- Code syntax highlighting
- Voice messages
- Chat export
- Settings page
- User profile management

---

## Notes
- All components should be mobile-responsive
- Follow accessibility best practices (WCAG)
- Use TypeScript strictly (no `any` types)
- Write self-documenting code with clear naming
- Keep components small and focused (single responsibility)

---

## Implementation Status

### ✅ Completed
- [x] shadcn/ui setup and configuration
- [x] Architecture restructuring with proper folder structure
- [x] Type definitions (auth, chat, api)
- [x] API service layer with mock data support
- [x] AuthContext and ChatContext implementation
- [x] Authentication UI (Login and Signup pages)
- [x] Optional authentication flow (users can use chat without auth)
- [x] Local storage support for unauthenticated users
- [x] Previous chats sidebar component (works for both auth and non-auth users)
- [x] Refactored chat components using shadcn/ui
- [x] Main chat page accessible without authentication
- [x] Auth prompts for features that require authentication

### 📝 Next Steps (Future Enhancements)
- [ ] Connect to real backend API (update `USE_MOCK_API` flag)
- [ ] Add chat search/filter functionality
- [ ] Implement chat title editing (inline editing)
- [ ] Add message editing/deletion
- [ ] Sync local chats to cloud when user authenticates
- [ ] Real-time updates (WebSockets)
- [ ] File upload support
- [ ] Markdown rendering in messages
- [ ] Settings page
- [ ] User profile management
- [ ] Export/import chats functionality

### 🔧 Configuration
To switch from mock API to real API:
1. Set `NEXT_PUBLIC_USE_MOCK_API=false` in `.env.local`
2. Update `NEXT_PUBLIC_API_URL` with your backend URL
3. Ensure backend endpoints match the expected format in `config/api.ts`

