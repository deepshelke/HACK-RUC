import { apiClient } from './client'
import { mockMessagesService } from './mock'
import { API_CONFIG, USE_MOCK_API } from '@/config/api'
import { Message } from '@/lib/types/chat'
import { ApiResponse } from '@/lib/types/api'

export const messagesApi = {
  async getMessages(chatId: string): Promise<ApiResponse<Message[]>> {
    if (USE_MOCK_API) {
      return mockMessagesService.getMessages(chatId)
    }
    return apiClient.get<Message[]>(API_CONFIG.endpoints.messages.list(chatId))
  },

  async createMessage(chatId: string, content: string, role: 'user' | 'assistant'): Promise<ApiResponse<Message>> {
    if (USE_MOCK_API) {
      return mockMessagesService.createMessage(chatId, content, role)
    }
    return apiClient.post<Message>(API_CONFIG.endpoints.messages.create(chatId), { content, role })
  },

  async updateMessage(chatId: string, messageId: string, content: string): Promise<ApiResponse<Message>> {
    if (USE_MOCK_API) {
      // Mock implementation
      const messages = (await mockMessagesService.getMessages(chatId)).data
      const message = messages.find(m => m.id === messageId)
      if (!message) throw { message: 'Message not found', status: 404 } as Error
      message.content = content
      return { data: message }
    }
    return apiClient.patch<Message>(API_CONFIG.endpoints.messages.update(chatId, messageId), { content })
  },

  async deleteMessage(chatId: string, messageId: string): Promise<ApiResponse<void>> {
    if (USE_MOCK_API) {
      // Mock implementation
      return { data: undefined }
    }
    return apiClient.delete<void>(API_CONFIG.endpoints.messages.delete(chatId, messageId))
  },
}

