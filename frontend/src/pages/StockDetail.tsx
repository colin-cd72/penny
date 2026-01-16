import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getStock, getPriceHistory, getStockNews } from '@/api/stocks'
import {
  formatCurrency,
  formatVolume,
  formatPercent,
  formatSignal,
  getSignalColor,
  getSignalBgColor,
  cn,
} from '@/lib/utils'
import { ArrowLeft, TrendingUp, TrendingDown, ExternalLink } from 'lucide-react'

export default function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>()

  const { data: stock, isLoading } = useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => getStock(symbol!),
    enabled: !!symbol,
  })

  const { data: news } = useQuery({
    queryKey: ['stock-news', symbol],
    queryFn: () => getStockNews(symbol!, 1, 10),
    enabled: !!symbol,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  if (!stock) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold">Stock not found</h2>
        <Link to="/" className="text-primary hover:underline mt-2 inline-block">
          Back to dashboard
        </Link>
      </div>
    )
  }

  const priceChange = stock.current_price && stock.previous_close
    ? stock.current_price - stock.previous_close
    : null
  const priceChangePercent = priceChange && stock.previous_close
    ? (priceChange / stock.previous_close) * 100
    : null
  const isPositive = priceChange !== null && priceChange >= 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            to="/"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold">{stock.symbol}</h1>
            <span
              className={cn(
                'px-3 py-1 rounded text-sm font-medium border',
                getSignalColor(stock.latest_signal),
                getSignalBgColor(stock.latest_signal)
              )}
            >
              {formatSignal(stock.latest_signal)}
            </span>
          </div>
          <p className="text-muted-foreground mt-1">{stock.name}</p>
        </div>

        <div className="text-right">
          <div className="text-3xl font-bold font-mono">
            {formatCurrency(stock.current_price)}
          </div>
          <div
            className={cn(
              'flex items-center justify-end gap-1 text-lg',
              isPositive ? 'text-green-500' : 'text-red-500'
            )}
          >
            {isPositive ? (
              <TrendingUp className="h-5 w-5" />
            ) : (
              <TrendingDown className="h-5 w-5" />
            )}
            {formatCurrency(priceChange)} ({formatPercent(priceChangePercent)})
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Price Chart Placeholder */}
          <div className="bg-card border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Price Chart</h2>
            <div className="h-80 flex items-center justify-center bg-muted/30 rounded">
              <p className="text-muted-foreground">
                Chart will be rendered here with Lightweight Charts
              </p>
            </div>
          </div>

          {/* Technical Indicators */}
          <div className="bg-card border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Technical Indicators</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">RSI (14)</div>
                <div className="text-lg font-mono">
                  {stock.indicators?.rsi_14?.toFixed(2) || '-'}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">MACD</div>
                <div className="text-lg font-mono">
                  {stock.indicators?.macd?.toFixed(4) || '-'}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">SMA 20</div>
                <div className="text-lg font-mono">
                  {formatCurrency(stock.indicators?.sma_20)}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">SMA 50</div>
                <div className="text-lg font-mono">
                  {formatCurrency(stock.indicators?.sma_50)}
                </div>
              </div>
            </div>
          </div>

          {/* News */}
          <div className="bg-card border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Recent News</h2>
            {news && news.length > 0 ? (
              <div className="space-y-4">
                {news.map((article) => (
                  <div key={article.id} className="border-b pb-4 last:border-0 last:pb-0">
                    <a
                      href={article.url || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-primary flex items-start gap-2"
                    >
                      <span className="font-medium">{article.title}</span>
                      <ExternalLink className="h-4 w-4 flex-shrink-0" />
                    </a>
                    <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                      <span>{article.source}</span>
                      {article.sentiment_label && (
                        <span
                          className={cn(
                            'px-2 py-0.5 rounded text-xs',
                            article.sentiment_label === 'positive' && 'bg-green-500/10 text-green-500',
                            article.sentiment_label === 'negative' && 'bg-red-500/10 text-red-500',
                            article.sentiment_label === 'neutral' && 'bg-gray-500/10 text-gray-500'
                          )}
                        >
                          {article.sentiment_label}
                        </span>
                      )}
                      <span>{new Date(article.published_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No recent news</p>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Stock Info */}
          <div className="bg-card border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Stock Info</h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Exchange</dt>
                <dd className="font-medium">{stock.exchange || '-'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Market Cap</dt>
                <dd className="font-medium">{formatVolume(stock.market_cap)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Volume</dt>
                <dd className="font-medium">{formatVolume(stock.volume)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Avg Volume (20d)</dt>
                <dd className="font-medium">{formatVolume(stock.avg_volume_20d)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Day High</dt>
                <dd className="font-medium">{formatCurrency(stock.day_high)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Day Low</dt>
                <dd className="font-medium">{formatCurrency(stock.day_low)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Sector</dt>
                <dd className="font-medium">{stock.sector || '-'}</dd>
              </div>
            </dl>
          </div>

          {/* Signal Details */}
          <div className="bg-card border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Signal Details</h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Signal</dt>
                <dd className={cn('font-medium', getSignalColor(stock.latest_signal))}>
                  {formatSignal(stock.latest_signal)}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Confidence</dt>
                <dd className="font-medium">
                  {stock.signal_confidence !== null
                    ? `${(stock.signal_confidence * 100).toFixed(0)}%`
                    : '-'}
                </dd>
              </div>
            </dl>

            <button className="w-full mt-4 py-2 px-4 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90">
              Trade {stock.symbol}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
