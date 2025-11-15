import { apiClient } from './client'
import { mockChatsService } from './mock'
import { API_CONFIG, USE_MOCK_API } from '@/config/api'
import { Chat } from '@/lib/types/chat'
import { ApiResponse } from '@/lib/types/api'

export const chatsApi = {
  async getChats(): Promise<ApiResponse<Chat[]>> {
    if (USE_MOCK_API) {
      const userId = typeof window !== 'undefined' 
        ? localStorage.getItem('user_id') || '1'
        : '1'
      return mockChatsService.getChats(userId)
    }
    return apiClient.get<Chat[]>(API_CONFIG.endpoints.chats.list)
  },

  async getChat(chatId: string): Promise<ApiResponse<Chat>> {
    if (USE_MOCK_API) {
      return mockChatsService.getChat(chatId)
    }
    return apiClient.get<Chat>(API_CONFIG.endpoints.chats.get(chatId))
  },

  async createChat(title?: string): Promise<ApiResponse<Chat>> {
    if (USE_MOCK_API) {
      const userId = typeof window !== 'undefined' 
        ? localStorage.getItem('user_id') || '1'
        : '1'
      return mockChatsService.createChat(userId, title)
    }
    return apiClient.post<Chat>(API_CONFIG.endpoints.chats.create, { title })
  },

  async updateChat(chatId: string, updates: Partial<Chat>): Promise<ApiResponse<Chat>> {
    if (USE_MOCK_API) {
      return mockChatsService.updateChat(chatId, updates)
    }
    return apiClient.patch<Chat>(API_CONFIG.endpoints.chats.update(chatId), updates)
  },

  async deleteChat(chatId: string): Promise<ApiResponse<void>> {
    if (USE_MOCK_API) {
      return mockChatsService.deleteChat(chatId)
    }
    return apiClient.delete<void>(API_CONFIG.endpoints.chats.delete(chatId))
  },
}

