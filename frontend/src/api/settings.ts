import apiClient from './client'

export interface APIKeyStatus {
  configured: boolean
  last_tested: string | null
  test_success: boolean | null
}

export interface APIKeyStatusResponse {
  polygon: APIKeyStatus
  sec_api: APIKeyStatus
  benzinga: APIKeyStatus
  alpha_vantage: APIKeyStatus
  reddit: APIKeyStatus
  alpaca: APIKeyStatus
  alpaca_paper_trading: boolean
  sendgrid: APIKeyStatus
  twilio: APIKeyStatus
  smtp: APIKeyStatus
  smtp_host: string | null
  smtp_port: string | null
  smtp_from_email: string | null
  smtp_use_tls: boolean
}

export interface APIKeyUpdate {
  polygon_api_key?: string
  sec_api_key?: string
  benzinga_api_key?: string
  alpha_vantage_api_key?: string
  reddit_client_id?: string
  reddit_client_secret?: string
  alpaca_api_key?: string
  alpaca_api_secret?: string
  alpaca_paper_trading?: boolean
  sendgrid_api_key?: string
  twilio_account_sid?: string
  twilio_auth_token?: string
  twilio_phone_number?: string
  smtp_host?: string
  smtp_port?: string
  smtp_username?: string
  smtp_password?: string
  smtp_from_email?: string
  smtp_use_tls?: boolean
}

export interface APIKeyTestResponse {
  service: string
  success: boolean
  message: string
  details?: Record<string, unknown>
}

export async function getAPIKeyStatus(): Promise<APIKeyStatusResponse> {
  const response = await apiClient.get<APIKeyStatusResponse>('/settings/api-keys')
  return response.data
}

export async function updateAPIKeys(keys: APIKeyUpdate): Promise<APIKeyStatusResponse> {
  const response = await apiClient.put<APIKeyStatusResponse>('/settings/api-keys', keys)
  return response.data
}

export async function testAPIKey(service: string): Promise<APIKeyTestResponse> {
  const response = await apiClient.post<APIKeyTestResponse>('/settings/api-keys/test', {
    service,
  })
  return response.data
}

export interface LoadStocksStatus {
  status: 'idle' | 'loading' | 'started' | 'completed' | 'error'
  message: string
  total_fetched?: number
  total_saved?: number
  current_page?: number
  started_at?: string
  completed_at?: string
}

export async function startLoadStocks(): Promise<LoadStocksStatus> {
  const response = await apiClient.post<LoadStocksStatus>('/settings/load-stocks')
  return response.data
}

export async function getLoadStocksStatus(): Promise<LoadStocksStatus> {
  const response = await apiClient.get<LoadStocksStatus>('/settings/load-stocks/status')
  return response.data
}
