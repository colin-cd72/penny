import apiClient from './client'

export interface Stock {
  id: string
  symbol: string
  name: string | null
  exchange: string | null
  current_price: number | null
  previous_close: number | null
  day_high: number | null
  day_low: number | null
  volume: number | null
  avg_volume_20d: number | null
  market_cap: number | null
  latest_signal: string | null
  signal_confidence: number | null
  rsi_14: number | null
  last_updated: string | null
}

export interface StockListResponse {
  items: Stock[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface PriceCandle {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  vwap: number | null
}

export interface TechnicalIndicators {
  symbol: string
  timestamp: string
  rsi_14: number | null
  rsi_7: number | null
  macd: number | null
  macd_signal: number | null
  macd_histogram: number | null
  sma_20: number | null
  sma_50: number | null
  sma_200: number | null
  ema_9: number | null
  ema_21: number | null
  bb_upper: number | null
  bb_middle: number | null
  bb_lower: number | null
  volume_sma_20: number | null
  obv: number | null
  atr_14: number | null
  stoch_k: number | null
  stoch_d: number | null
}

export interface StockDetail extends Stock {
  market_tier: string | null
  sector: string | null
  industry: string | null
  cik: string | null
  indicators: TechnicalIndicators | null
  recent_prices: PriceCandle[] | null
}

interface ListStocksParams {
  page?: number
  per_page?: number
  sector?: string
  exchange?: string
  min_price?: number
  max_price?: number
  min_volume?: number
  signal?: string
  min_confidence?: number
  sort_by?: string
  order?: 'asc' | 'desc'
  search?: string
}

export async function listStocks(params: ListStocksParams = {}): Promise<StockListResponse> {
  const response = await apiClient.get<StockListResponse>('/stocks', { params })
  return response.data
}

export async function getStock(symbol: string): Promise<StockDetail> {
  const response = await apiClient.get<StockDetail>(`/stocks/${symbol}`)
  return response.data
}

export async function getPriceHistory(
  symbol: string,
  interval: string = '1d',
  limit: number = 500
): Promise<PriceCandle[]> {
  const response = await apiClient.get<PriceCandle[]>(`/stocks/${symbol}/price-history`, {
    params: { interval, limit },
  })
  return response.data
}

export async function getTechnicalIndicators(symbol: string): Promise<TechnicalIndicators> {
  const response = await apiClient.get<TechnicalIndicators>(`/stocks/${symbol}/indicators`)
  return response.data
}

export interface NewsArticle {
  id: string
  title: string
  summary: string | null
  source: string | null
  url: string | null
  sentiment_score: number | null
  sentiment_label: string | null
  published_at: string
}

export async function getStockNews(
  symbol: string,
  page: number = 1,
  per_page: number = 20
): Promise<NewsArticle[]> {
  const response = await apiClient.get<NewsArticle[]>(`/stocks/${symbol}/news`, {
    params: { page, per_page },
  })
  return response.data
}
