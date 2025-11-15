export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  createdAt: Date
}

export interface AuthResponse {
  user: User
  token: string
  refreshToken?: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface SignupCredentials {
  email: string
  password: string
  name: string
}

