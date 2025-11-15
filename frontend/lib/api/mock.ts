import { AuthResponse, LoginCredentials, SignupCredentials, User } from '@/lib/types/auth'
import { Chat, Message } from '@/lib/types/chat'
import { ApiResponse } from '@/lib/types/api'

// Mock data storage (simulates a database)
let mockUsers: User[] = [
  {
    id: '1',
    email: 'demo@example.com',
    name: 'Demo User',
    createdAt: new Date(),
  },
]

let mockChats: Chat[] = []
let mockMessages: Message[] = []

// Mock delay to simulate API calls
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export const mockAuth = {
  async login(credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> {
    await delay(800)
    
    const user = mockUsers.find(u => u.email === credentials.email)
    if (!user || credentials.password !== 'password') {
      throw { message: 'Invalid credentials', status: 401 } as Error
    }

    return {
      data: {
        user,
        token: 'mock_token_' + Date.now(),
      },
    }
  },

  async signup(credentials: SignupCredentials): Promise<ApiResponse<AuthResponse>> {
    await delay(800)
    
    const existingUser = mockUsers.find(u => u.email === credentials.email)
    if (existingUser) {
      throw { message: 'User already exists', status: 400 } as Error
    }

    const newUser: User = {
      id: Date.now().toString(),
      email: credentials.email,
      name: credentials.name,
      createdAt: new Date(),
    }

    mockUsers.push(newUser)

    return {
      data: {
        user: newUser,
        token: 'mock_token_' + Date.now(),
      },
    }
  },

  async getCurrentUser(token: string): Promise<ApiResponse<User>> {
    await delay(300)
    
    // In real app, token would be validated
    const user = mockUsers[0] // Simplified
    return { data: user }
  },
}

export const mockChatsService = {
  async getChats(userId: string): Promise<ApiResponse<Chat[]>> {
    await delay(500)
    const userChats = mockChats.filter(c => c.userId === userId)
    return { data: userChats }
  },

  async getChat(chatId: string): Promise<ApiResponse<Chat>> {
    await delay(300)
    const chat = mockChats.find(c => c.id === chatId)
    if (!chat) {
      throw { message: 'Chat not found', status: 404 } as Error
    }
    return { data: chat }
  },

  async createChat(userId: string, title?: string): Promise<ApiResponse<Chat>> {
    await delay(400)
    const newChat: Chat = {
      id: Date.now().toString(),
      title: title || `New Chat ${mockChats.length + 1}`,
      createdAt: new Date(),
      updatedAt: new Date(),
      messageCount: 0,
      userId,
    }
    mockChats.push(newChat)
    return { data: newChat }
  },

  async updateChat(chatId: string, updates: Partial<Chat>): Promise<ApiResponse<Chat>> {
    await delay(300)
    const chatIndex = mockChats.findIndex(c => c.id === chatId)
    if (chatIndex === -1) {
      throw { message: 'Chat not found', status: 404 } as Error
    }
    mockChats[chatIndex] = { ...mockChats[chatIndex], ...updates, updatedAt: new Date() }
    return { data: mockChats[chatIndex] }
  },

  async deleteChat(chatId: string): Promise<ApiResponse<void>> {
    await delay(300)
    const chatIndex = mockChats.findIndex(c => c.id === chatId)
    if (chatIndex === -1) {
      throw { message: 'Chat not found', status: 404 } as Error
    }
    mockChats.splice(chatIndex, 1)
    mockMessages = mockMessages.filter(m => m.chatId !== chatId)
    return { data: undefined }
  },
}

export const mockMessagesService = {
  async getMessages(chatId: string): Promise<ApiResponse<Message[]>> {
    await delay(400)
    const messages = mockMessages.filter(m => m.chatId === chatId)
    return { data: messages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime()) }
  },

  async createMessage(chatId: string, content: string, role: 'user' | 'assistant'): Promise<ApiResponse<Message>> {
    await delay(600)
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      role,
      timestamp: new Date(),
      chatId,
    }
    mockMessages.push(newMessage)

    // Update chat's last message
    const chatIndex = mockChats.findIndex(c => c.id === chatId)
    if (chatIndex !== -1) {
      mockChats[chatIndex].lastMessage = content.substring(0, 100)
      mockChats[chatIndex].lastMessageAt = new Date()
      mockChats[chatIndex].messageCount = mockMessages.filter(m => m.chatId === chatId).length
      mockChats[chatIndex].updatedAt = new Date()
    }

    return { data: newMessage }
  },
}

