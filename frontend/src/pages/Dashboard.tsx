import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listStocks, type Stock } from '@/api/stocks'
import {
  formatCurrency,
  formatVolume,
  formatPercent,
  formatSignal,
  getSignalColor,
  getSignalBgColor,
  cn,
} from '@/lib/utils'
import { TrendingUp, TrendingDown, Search, RefreshCw } from 'lucide-react'

export default function Dashboard() {
  const [search, setSearch] = useState('')
  const [signalFilter, setSignalFilter] = useState<string>('')
  const [page, setPage] = useState(1)

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['stocks', page, signalFilter, search],
    queryFn: () =>
      listStocks({
        page,
        per_page: 25,
        signal: signalFilter || undefined,
        search: search || undefined,
        sort_by: 'signal_confidence',
        order: 'desc',
      }),
  })

  const getPriceChangePercent = (stock: Stock) => {
    if (!stock.current_price || !stock.previous_close) return null
    return ((stock.current_price - stock.previous_close) / stock.previous_close) * 100
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Monitor penny stocks and trading signals</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by symbol or name..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            className="w-full pl-10 pr-4 py-2 border rounded-md bg-background"
          />
        </div>
        <select
          value={signalFilter}
          onChange={(e) => {
            setSignalFilter(e.target.value)
            setPage(1)
          }}
          className="px-4 py-2 border rounded-md bg-background"
        >
          <option value="">All Signals</option>
          <option value="strong_buy">Strong Buy</option>
          <option value="buy">Buy</option>
          <option value="hold">Hold</option>
          <option value="sell">Sell</option>
          <option value="strong_sell">Strong Sell</option>
        </select>
      </div>

      {/* Stock Table */}
      <div className="bg-card border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Symbol</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Price</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Change</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Volume</th>
                <th className="px-4 py-3 text-center text-sm font-medium">Signal</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Confidence</th>
                <th className="px-4 py-3 text-right text-sm font-medium">RSI</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    Loading...
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    No stocks found
                  </td>
                </tr>
              ) : (
                data?.items.map((stock) => {
                  const changePercent = getPriceChangePercent(stock)
                  const isPositive = changePercent !== null && changePercent >= 0

                  return (
                    <tr key={stock.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <Link
                          to={`/stocks/${stock.symbol}`}
                          className="hover:text-primary"
                        >
                          <div className="font-medium">{stock.symbol}</div>
                          <div className="text-sm text-muted-foreground truncate max-w-[200px]">
                            {stock.name}
                          </div>
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-right font-mono">
                        {formatCurrency(stock.current_price)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div
                          className={cn(
                            'flex items-center justify-end gap-1',
                            isPositive ? 'text-green-500' : 'text-red-500'
                          )}
                        >
                          {isPositive ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <TrendingDown className="h-4 w-4" />
                          )}
                          {formatPercent(changePercent)}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-mono">
                        {formatVolume(stock.volume)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={cn(
                            'inline-block px-2 py-1 rounded text-xs font-medium border',
                            getSignalColor(stock.latest_signal),
                            getSignalBgColor(stock.latest_signal)
                          )}
                        >
                          {formatSignal(stock.latest_signal)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {stock.signal_confidence !== null
                          ? `${(stock.signal_confidence * 100).toFixed(0)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-right font-mono">
                        {stock.rsi_14?.toFixed(1) || '-'}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {(page - 1) * data.per_page + 1} to{' '}
              {Math.min(page * data.per_page, data.total)} of {data.total}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded-md disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="px-3 py-1 border rounded-md disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
