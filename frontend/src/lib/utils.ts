import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return '-'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value)
}

export function formatNumber(value: number | null | undefined, decimals = 2): string {
  if (value == null) return '-'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatPercent(value: number | null | undefined, decimals = 2): string {
  if (value == null) return '-'
  return `${value >= 0 ? '+' : ''}${formatNumber(value, decimals)}%`
}

export function formatVolume(value: number | null | undefined): string {
  if (value == null) return '-'
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}B`
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(2)}K`
  }
  return value.toString()
}

export function formatMarketCap(value: number | null | undefined): string {
  return formatVolume(value)
}

export function getSignalColor(signal: string | null): string {
  switch (signal) {
    case 'strong_buy':
      return 'text-green-500'
    case 'buy':
      return 'text-green-400'
    case 'hold':
      return 'text-yellow-500'
    case 'sell':
      return 'text-red-400'
    case 'strong_sell':
      return 'text-red-500'
    default:
      return 'text-gray-500'
  }
}

export function getSignalBgColor(signal: string | null): string {
  switch (signal) {
    case 'strong_buy':
      return 'bg-green-500/10 border-green-500/20'
    case 'buy':
      return 'bg-green-400/10 border-green-400/20'
    case 'hold':
      return 'bg-yellow-500/10 border-yellow-500/20'
    case 'sell':
      return 'bg-red-400/10 border-red-400/20'
    case 'strong_sell':
      return 'bg-red-500/10 border-red-500/20'
    default:
      return 'bg-gray-500/10 border-gray-500/20'
  }
}

export function formatSignal(signal: string | null): string {
  if (!signal) return '-'
  return signal.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}
