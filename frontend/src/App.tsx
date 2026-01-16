import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authSlice'
import Layout from '@/components/Layout'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Dashboard from '@/pages/Dashboard'
import StockDetail from '@/pages/StockDetail'
import Watchlists from '@/pages/Watchlists'
import Portfolio from '@/pages/Portfolio'
import TradeHistory from '@/pages/TradeHistory'
import Settings from '@/pages/Settings'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="stocks/:symbol" element={<StockDetail />} />
        <Route path="watchlists" element={<Watchlists />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="trades" element={<TradeHistory />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
