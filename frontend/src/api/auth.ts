import apiClient from './client'

interface LoginCredentials {
  email: string
  password: string
}

interface RegisterData {
  email: string
  password: string
  full_name?: string
  phone_number?: string
}

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

interface User {
  id: string
  email: string
  full_name: string | null
  phone_number: string | null
  is_active: boolean
  is_verified: boolean
  role: string
  settings: Record<string, unknown>
  created_at: string
}

export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/login', credentials)
  return response.data
}

export async function register(data: RegisterData): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', data)
  return response.data
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me')
  return response.data
}

export async function updateMe(data: Partial<User>): Promise<User> {
  const response = await apiClient.put<User>('/auth/me', data)
  return response.data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}
