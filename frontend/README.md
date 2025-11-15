# Fairly Frontend

A modern chat UI inspired by Gemini, built with Next.js, TypeScript, Tailwind CSS, and shadcn/ui.

## Features

- 🎨 **Modern UI**: Clean, Gemini-inspired design with shadcn/ui components
- 🔓 **No Auth Required**: Use chat immediately without signing in
- 💾 **Local Storage**: Chats persist in browser for unauthenticated users
- 🔐 **Optional Authentication**: Sign in to sync chats across devices
- 💬 **Chat Interface**: Real-time chat with message history
- 📋 **Previous Chats**: Sidebar showing all previous conversations (local or synced)
- 🌙 **Dark Mode**: Built-in dark mode support
- 📱 **Responsive**: Mobile-friendly design
- ⚡ **Fast**: Built with Next.js 14 and React 18
- 🎯 **Type Safe**: Full TypeScript support
- 🏗️ **Scalable Architecture**: Easy to extend and maintain

## Architecture

The project follows a clean, maintainable architecture:

```
frontend/
├── app/                    # Next.js app router
│   ├── (auth)/            # Authentication routes
│   ├── (chat)/            # Protected chat routes
│   └── layout.tsx         # Root layout with providers
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── auth/              # Auth components
│   └── chat/              # Chat components
├── lib/
│   ├── api/               # API service layer
│   ├── contexts/          # React contexts (Auth, Chat)
│   ├── types/             # TypeScript types
│   └── utils/             # Utility functions
└── config/                # Configuration files
```

### Key Architectural Decisions

- **Service Layer**: All API calls abstracted into service functions
- **Context API**: Global state management for auth and chat
- **Type Safety**: Centralized type definitions
- **Mock API**: Easy toggle between mock and real API for development

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Usage

**Without Authentication:**
- You can start using the chat immediately without signing in
- Your chats are saved in browser local storage
- Chats persist across page refreshes but are device-specific

**With Authentication:**
- Sign in to sync chats across devices
- Access your chats from any device
- Default mock credentials (if using mock API):
  - Email: `demo@example.com`
  - Password: `password`
- Or create a new account using the signup page

## API Integration

### Mock Mode (Default)

The app runs in mock mode by default, which simulates API responses. This is perfect for development and testing.

### Connecting to Real Backend

1. Create a `.env.local` file in the `frontend` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK_API=false
```

2. Ensure your backend API matches the expected endpoints:
   - See `config/api.ts` for endpoint definitions
   - Authentication: `/api/auth/*`
   - Chats: `/api/chats/*`
   - Messages: `/api/chats/:id/messages/*`

3. The API client automatically handles:
   - Authentication tokens
   - Request/response formatting
   - Error handling

## Project Structure

### Components

- **UI Components** (`components/ui/`): Reusable shadcn/ui components
- **Auth Components** (`components/auth/`): Login and signup forms
- **Chat Components** (`components/chat/`): Chat-specific components

### Services

- **API Client** (`lib/api/client.ts`): Base HTTP client
- **Auth API** (`lib/api/auth.ts`): Authentication endpoints
- **Chats API** (`lib/api/chats.ts`): Chat management
- **Messages API** (`lib/api/messages.ts`): Message operations
- **Mock API** (`lib/api/mock.ts`): Mock data for development

### Contexts

- **AuthContext**: User authentication state
- **ChatContext**: Current chat and messages state

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Customization

### Styling

The project uses Tailwind CSS with shadcn/ui. Customize themes in:
- `tailwind.config.js` - Tailwind configuration
- `app/globals.css` - Global styles and CSS variables

### Adding New Components

Use shadcn/ui CLI to add new components:
```bash
npx shadcn-ui@latest add [component-name]
```

## Development Notes

- All components are mobile-responsive
- Follows accessibility best practices
- TypeScript strict mode enabled
- Components are small and focused (single responsibility)

## Future Enhancements

See `IMPLEMENTATION_PLAN.md` for detailed roadmap including:
- Real-time messaging (WebSockets)
- File uploads
- Markdown rendering
- Chat search/filter
- Settings page
- And more...

## License

MIT
