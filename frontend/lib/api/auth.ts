import { apiClient } from './client'
import { mockAuth } from './mock'
import { API_CONFIG, USE_MOCK_API } from '@/config/api'
import { AuthResponse, LoginCredentials, SignupCredentials, User } from '@/lib/types/auth'
import { ApiResponse } from '@/lib/types/api'

export const authApi = {
  async login(credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> {
    if (USE_MOCK_API) {
      return mockAuth.login(credentials)
    }
    return apiClient.post<AuthResponse>(API_CONFIG.endpoints.auth.login, credentials)
  },

  async signup(credentials: SignupCredentials): Promise<ApiResponse<AuthResponse>> {
    if (USE_MOCK_API) {
      return mockAuth.signup(credentials)
    }
    return apiClient.post<AuthResponse>(API_CONFIG.endpoints.auth.signup, credentials)
  },

  async logout(): Promise<ApiResponse<void>> {
    if (USE_MOCK_API) {
      return { data: undefined }
    }
    return apiClient.post<void>(API_CONFIG.endpoints.auth.logout)
  },

  async getCurrentUser(): Promise<ApiResponse<User>> {
    if (USE_MOCK_API) {
      const token = typeof window !== 'undefined' 
        ? localStorage.getItem('auth_token') 
        : null
      if (!token) throw { message: 'Not authenticated', status: 401 } as Error
      return mockAuth.getCurrentUser(token)
    }
    return apiClient.get<User>(API_CONFIG.endpoints.auth.me)
  },

  async refreshToken(): Promise<ApiResponse<{ token: string }>> {
    if (USE_MOCK_API) {
      return { data: { token: 'mock_token_' + Date.now() } }
    }
    return apiClient.post<{ token: string }>(API_CONFIG.endpoints.auth.refresh)
  },
}

