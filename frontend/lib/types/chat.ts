export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  chatId: string
}

export interface Chat {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  lastMessage?: string
  lastMessageAt?: Date
  messageCount: number
  userId: string
}

export interface ChatWithMessages extends Chat {
  messages: Message[]
}

