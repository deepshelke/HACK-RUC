export const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  endpoints: {
    auth: {
      login: '/api/auth/login',
      signup: '/api/auth/signup',
      logout: '/api/auth/logout',
      me: '/api/auth/me',
      refresh: '/api/auth/refresh',
    },
    chats: {
      list: '/api/chats',
      get: (id: string) => `/api/chats/${id}`,
      create: '/api/chats',
      update: (id: string) => `/api/chats/${id}`,
      delete: (id: string) => `/api/chats/${id}`,
    },
    messages: {
      list: (chatId: string) => `/api/chats/${chatId}/messages`,
      create: (chatId: string) => `/api/chats/${chatId}/messages`,
      update: (chatId: string, messageId: string) => `/api/chats/${chatId}/messages/${messageId}`,
      delete: (chatId: string, messageId: string) => `/api/chats/${chatId}/messages/${messageId}`,
    },
  },
}

// Mock mode flag - set to false when connecting to real API
export const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API !== 'false'

