'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { Chat, Message } from '@/lib/types/chat'
import { chatsApi } from '@/lib/api/chats'
import { messagesApi } from '@/lib/api/messages'
import { useAuth } from './AuthContext'

interface ChatContextType {
  chats: Chat[]
  currentChat: Chat | null
  messages: Message[]
  isLoading: boolean
  isSending: boolean
  createChat: () => Promise<Chat>
  selectChat: (chatId: string) => Promise<void>
  deleteChat: (chatId: string) => Promise<void>
  updateChatTitle: (chatId: string, title: string) => Promise<void>
  sendMessage: (content: string) => Promise<void>
  refreshChats: () => Promise<void>
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

const LOCAL_STORAGE_KEY = 'hack_ruc_local_chats'
const LOCAL_STORAGE_MESSAGES_KEY = 'hack_ruc_local_messages'
const LOCAL_STORAGE_CURRENT_CHAT_KEY = 'hack_ruc_current_chat'

// Helper functions for local storage
const getLocalChats = (): Chat[] => {
  if (typeof window === 'undefined') return []
  const stored = localStorage.getItem(LOCAL_STORAGE_KEY)
  if (!stored) return []
  
  const parsed = JSON.parse(stored)
  // Convert date strings back to Date objects
  return parsed.map((chat: any) => ({
    ...chat,
    createdAt: new Date(chat.createdAt),
    updatedAt: new Date(chat.updatedAt),
    lastMessageAt: chat.lastMessageAt ? new Date(chat.lastMessageAt) : undefined,
  }))
}

const saveLocalChats = (chats: Chat[]) => {
  if (typeof window === 'undefined') return
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(chats))
}

const getLocalMessages = (): Message[] => {
  if (typeof window === 'undefined') return []
  const stored = localStorage.getItem(LOCAL_STORAGE_MESSAGES_KEY)
  if (!stored) return []
  
  const parsed = JSON.parse(stored)
  // Convert date strings back to Date objects
  return parsed.map((message: any) => ({
    ...message,
    timestamp: new Date(message.timestamp),
  }))
}

const saveLocalMessages = (messages: Message[]) => {
  if (typeof window === 'undefined') return
  localStorage.setItem(LOCAL_STORAGE_MESSAGES_KEY, JSON.stringify(messages))
}

const getLocalCurrentChat = (): string | null => {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(LOCAL_STORAGE_CURRENT_CHAT_KEY)
}

const saveLocalCurrentChat = (chatId: string | null) => {
  if (typeof window === 'undefined') return
  if (chatId) {
    localStorage.setItem(LOCAL_STORAGE_CURRENT_CHAT_KEY, chatId)
  } else {
    localStorage.removeItem(LOCAL_STORAGE_CURRENT_CHAT_KEY)
  }
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const [chats, setChats] = useState<Chat[]>([])
  const [currentChat, setCurrentChat] = useState<Chat | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)

  // Load local chats on mount for unauthenticated users
  useEffect(() => {
    if (!isAuthenticated) {
      const localChats = getLocalChats()
      setChats(localChats)
      
      const currentChatId = getLocalCurrentChat()
      if (currentChatId) {
        const chat = localChats.find(c => c.id === currentChatId)
        if (chat) {
          setCurrentChat(chat)
          const localMessages = getLocalMessages().filter(m => m.chatId === currentChatId)
          setMessages(localMessages)
        }
      }
    }
  }, [isAuthenticated])

  // Load chats from API when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      refreshChats()
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (currentChat) {
      if (isAuthenticated) {
        loadMessages(currentChat.id)
      } else {
        // For unauthenticated users, load from local storage
        const localMessages = getLocalMessages().filter(m => m.chatId === currentChat.id)
        setMessages(localMessages)
      }
    } else {
      setMessages([])
    }
  }, [currentChat, isAuthenticated])

  // Helper to normalize dates from API responses (JSON serializes dates as strings)
  const normalizeChatDates = (chat: any): Chat => ({
    ...chat,
    createdAt: new Date(chat.createdAt),
    updatedAt: new Date(chat.updatedAt),
    lastMessageAt: chat.lastMessageAt ? new Date(chat.lastMessageAt) : undefined,
  })

  const normalizeMessageDates = (message: any): Message => ({
    ...message,
    timestamp: new Date(message.timestamp),
  })

  const refreshChats = async () => {
    if (!isAuthenticated) return
    
    try {
      setIsLoading(true)
      const response = await chatsApi.getChats()
      // Normalize dates from API response
      setChats(response.data.map(normalizeChatDates))
    } catch (error) {
      console.error('Failed to load chats:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadMessages = async (chatId: string) => {
    if (!isAuthenticated) return
    
    try {
      setIsLoading(true)
      const response = await messagesApi.getMessages(chatId)
      // Normalize dates from API response
      setMessages(response.data.map(normalizeMessageDates))
    } catch (error) {
      console.error('Failed to load messages:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const createChat = async (): Promise<Chat> => {
    const newChat: Chat = {
      id: `local-${Date.now()}`,
      title: `New Chat ${(isAuthenticated ? chats.length : getLocalChats().length) + 1}`,
      createdAt: new Date(),
      updatedAt: new Date(),
      messageCount: 0,
      userId: isAuthenticated ? 'authenticated' : 'anonymous',
    }

    if (isAuthenticated) {
      try {
        const response = await chatsApi.createChat()
        // Normalize dates from API response
        const serverChat = normalizeChatDates(response.data)
        setChats(prev => [serverChat, ...prev])
        setCurrentChat(serverChat)
        setMessages([])
        return serverChat
      } catch (error) {
        console.error('Failed to create chat on server:', error)
        // Fallback to local chat
      }
    }

    // Create local chat (for unauthenticated or as fallback)
    const updatedChats = [newChat, ...(isAuthenticated ? chats : getLocalChats())]
    setChats(updatedChats)
    if (!isAuthenticated) {
      saveLocalChats(updatedChats)
    }
    setCurrentChat(newChat)
    setMessages([])
    saveLocalCurrentChat(newChat.id)
    return newChat
  }

  const selectChat = async (chatId: string) => {
    if (isAuthenticated) {
      try {
        const response = await chatsApi.getChat(chatId)
        // Normalize dates from API response
        setCurrentChat(normalizeChatDates(response.data))
        saveLocalCurrentChat(chatId)
        return
      } catch (error) {
        console.error('Failed to load chat:', error)
        throw error
      }
    }

    // For unauthenticated users, find in local chats
    const chat = chats.find(c => c.id === chatId)
    if (chat) {
      setCurrentChat(chat)
      saveLocalCurrentChat(chatId)
      const localMessages = getLocalMessages().filter(m => m.chatId === chatId)
      setMessages(localMessages)
    }
  }

  const deleteChat = async (chatId: string) => {
    if (isAuthenticated) {
      try {
        await chatsApi.deleteChat(chatId)
      } catch (error) {
        console.error('Failed to delete chat on server:', error)
      }
    }

    // Remove from local state and storage
    const updatedChats = chats.filter(c => c.id !== chatId)
    setChats(updatedChats)
    
    if (!isAuthenticated) {
      saveLocalChats(updatedChats)
      const localMessages = getLocalMessages().filter(m => m.chatId !== chatId)
      saveLocalMessages(localMessages)
    }

    if (currentChat?.id === chatId) {
      setCurrentChat(null)
      setMessages([])
      saveLocalCurrentChat(null)
    }
  }

  const updateChatTitle = async (chatId: string, title: string) => {
    if (isAuthenticated) {
      try {
        const response = await chatsApi.updateChat(chatId, { title })
        // Normalize dates from API response
        const updatedChat = normalizeChatDates(response.data)
        setChats(prev => prev.map(c => c.id === chatId ? updatedChat : c))
        if (currentChat?.id === chatId) {
          setCurrentChat(updatedChat)
        }
        return
      } catch (error) {
        console.error('Failed to update chat on server:', error)
      }
    }

    // Update local chat
    const updatedChats = chats.map(c => 
      c.id === chatId ? { ...c, title, updatedAt: new Date() } : c
    )
    setChats(updatedChats)
    if (!isAuthenticated) {
      saveLocalChats(updatedChats)
    }
    if (currentChat?.id === chatId) {
      setCurrentChat(updatedChats.find(c => c.id === chatId) || null)
    }
  }

  const sendMessage = async (content: string) => {
    if (!currentChat || !content.trim()) return

    try {
      setIsSending(true)

      // Add user message immediately
      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        content: content.trim(),
        role: 'user',
        timestamp: new Date(),
        chatId: currentChat.id,
      }
      setMessages(prev => [...prev, userMessage])

      // Save to local storage for unauthenticated users
      if (!isAuthenticated) {
        const localMessages = getLocalMessages()
        localMessages.push(userMessage)
        saveLocalMessages(localMessages)
      } else {
        // Save user message to API
        await messagesApi.createMessage(currentChat.id, content.trim(), 'user')
      }

      // Simulate assistant response (replace with actual API call)
      await new Promise(resolve => setTimeout(resolve, 1000))
      const assistantResponse = `This is a simulated response to: "${content}". In a real implementation, this would connect to your backend API.`
      
      const assistantMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        content: assistantResponse,
        role: 'assistant',
        timestamp: new Date(),
        chatId: currentChat.id,
      }
      setMessages(prev => [...prev, assistantMessage])

      // Save assistant message
      if (!isAuthenticated) {
        const localMessages = getLocalMessages()
        localMessages.push(assistantMessage)
        saveLocalMessages(localMessages)
      } else {
        await messagesApi.createMessage(currentChat.id, assistantResponse, 'assistant')
      }

      // Update chat's last message
      const updatedChat = {
        ...currentChat,
        lastMessage: assistantResponse.substring(0, 100),
        lastMessageAt: new Date(),
        messageCount: messages.length + 2,
        updatedAt: new Date(),
      }
      setCurrentChat(updatedChat)
      const updatedChats = chats.map(c => c.id === currentChat.id ? updatedChat : c)
      setChats(updatedChats)
      
      if (!isAuthenticated) {
        saveLocalChats(updatedChats)
      } else {
        await refreshChats()
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      throw error
    } finally {
      setIsSending(false)
    }
  }

  return (
    <ChatContext.Provider
      value={{
        chats,
        currentChat,
        messages,
        isLoading,
        isSending,
        createChat,
        selectChat,
        deleteChat,
        updateChatTitle,
        sendMessage,
        refreshChats,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
}
