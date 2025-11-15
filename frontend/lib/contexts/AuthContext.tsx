'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User, LoginCredentials, SignupCredentials } from '@/lib/types/auth'
import { authApi } from '@/lib/api/auth'
import { STORAGE_KEYS } from '@/lib/utils/constants'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  signup: (credentials: SignupCredentials) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing auth token on mount
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
    if (token) {
      refreshUser().catch(() => {
        // If refresh fails, clear auth
        localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
        localStorage.removeItem(STORAGE_KEYS.USER)
        setUser(null)
        setIsLoading(false)
      })
    } else {
      setIsLoading(false)
    }
  }, [])

  const refreshUser = async () => {
    try {
      const response = await authApi.getCurrentUser()
      setUser(response.data)
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.data))
      if (response.data.id) {
        localStorage.setItem('user_id', response.data.id)
      }
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true)
    try {
      const response = await authApi.login(credentials)
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, response.data.token)
      setUser(response.data.user)
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.data.user))
      if (response.data.user.id) {
        localStorage.setItem('user_id', response.data.user.id)
      }
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const signup = async (credentials: SignupCredentials) => {
    setIsLoading(true)
    try {
      const response = await authApi.signup(credentials)
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, response.data.token)
      setUser(response.data.user)
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.data.user))
      if (response.data.user.id) {
        localStorage.setItem('user_id', response.data.user.id)
      }
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      await authApi.logout()
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.USER)
      localStorage.removeItem('user_id')
      setUser(null)
      setIsLoading(false)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

