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

const LOCAL_STORAGE_KEY = 'fairly_local_chats'
const LOCAL_STORAGE_MESSAGES_KEY = 'fairly_local_messages'
const LOCAL_STORAGE_CURRENT_CHAT_KEY = 'fairly_current_chat'

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

  // Load chats from API on mount (backend doesn't require auth)
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        await refreshChats()
      } catch (error) {
        console.error('Failed to load chats:', error)
        // Fallback to local storage if API fails
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
    }
    loadInitialData()
  }, [])

  useEffect(() => {
    if (currentChat) {
      loadMessages(currentChat.id)
    } else {
      setMessages([])
    }
  }, [currentChat])

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
    try {
      setIsLoading(true)
      const response = await chatsApi.getChats()
      // Normalize dates from API response
      setChats(response.data.map(normalizeChatDates))
    } catch (error) {
      console.error('Failed to load chats:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const loadMessages = async (chatId: string) => {
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
    try {
      const response = await chatsApi.createChat()
      // Normalize dates from API response
      const serverChat = normalizeChatDates(response.data)
      setChats(prev => [serverChat, ...prev])
      setCurrentChat(serverChat)
      setMessages([])
      saveLocalCurrentChat(serverChat.id)
      return serverChat
    } catch (error) {
      console.error('Failed to create chat:', error)
      throw error
    }
  }

  const selectChat = async (chatId: string) => {
    try {
      const response = await chatsApi.getChat(chatId)
      // Normalize dates from API response
      setCurrentChat(normalizeChatDates(response.data))
      saveLocalCurrentChat(chatId)
    } catch (error) {
      console.error('Failed to load chat:', error)
      // Fallback to finding in current chats list
      const chat = chats.find(c => c.id === chatId)
      if (chat) {
        setCurrentChat(chat)
        saveLocalCurrentChat(chatId)
      } else {
        throw error
      }
    }
  }

  const deleteChat = async (chatId: string) => {
    try {
      await chatsApi.deleteChat(chatId)
    } catch (error) {
      console.error('Failed to delete chat:', error)
      // Continue with local deletion even if API fails
    }

    // Remove from local state
    const updatedChats = chats.filter(c => c.id !== chatId)
    setChats(updatedChats)

    if (currentChat?.id === chatId) {
      setCurrentChat(null)
      setMessages([])
      saveLocalCurrentChat(null)
    }
  }

  const updateChatTitle = async (chatId: string, title: string) => {
    try {
      const response = await chatsApi.updateChat(chatId, { title })
      // Normalize dates from API response
      const updatedChat = normalizeChatDates(response.data)
      setChats(prev => prev.map(c => c.id === chatId ? updatedChat : c))
      if (currentChat?.id === chatId) {
        setCurrentChat(updatedChat)
      }
    } catch (error) {
      console.error('Failed to update chat:', error)
      throw error
    }
  }

  const sendMessage = async (content: string) => {
    if (!currentChat || !content.trim()) return

    const chatId = currentChat.id // Store chatId to avoid closure issues

    try {
      setIsSending(true)

      // Send user message to API (triggers AI response in background)
      const response = await messagesApi.createMessage(chatId, content.trim(), 'user')
      const userMessage = normalizeMessageDates(response.data)
      
      // Add user message to UI immediately
      setMessages(prev => [...prev, userMessage])

      // Poll for AI response (generated in background)
      const pollForAIResponse = () => {
        const maxAttempts = 15 // Poll for up to 30 seconds (15 * 2s)
        let attempts = 0
        
        const pollInterval = setInterval(async () => {
          attempts++
          
          try {
            const messagesResponse = await messagesApi.getMessages(chatId)
            const allMessages = messagesResponse.data.map(normalizeMessageDates)
            
            // Check if AI response has arrived
            const hasAssistantMessage = allMessages.some(
              msg => msg.role === 'assistant' && 
              new Date(msg.timestamp) > new Date(userMessage.timestamp)
            )
            
            if (hasAssistantMessage || attempts >= maxAttempts) {
              clearInterval(pollInterval)
              
              // Update messages with latest from server
              setMessages(allMessages)
              
              // Refresh chat to get updated metadata
              try {
                await refreshChats()
                
                // Update current chat if it's still selected
                const updatedChatsResponse = await chatsApi.getChats()
                const updatedChat = updatedChatsResponse.data
                  .map(normalizeChatDates)
                  .find(c => c.id === chatId)
                if (updatedChat) {
                  setCurrentChat(updatedChat)
                }
              } catch (error) {
                console.error('Error refreshing chat:', error)
              } finally {
                // Stop showing loading indicator
                setIsSending(false)
              }
            }
          } catch (error) {
            console.error('Error polling for AI response:', error)
            if (attempts >= maxAttempts) {
              clearInterval(pollInterval)
              setIsSending(false)
            }
          }
        }, 2000) // Poll every 2 seconds
        
        // Store interval ID for cleanup if needed
        return pollInterval
      }

      // Start polling for AI response
      pollForAIResponse()

    } catch (error) {
      console.error('Failed to send message:', error)
      setIsSending(false)
      throw error
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
