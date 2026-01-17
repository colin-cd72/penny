import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAPIKeyStatus, updateAPIKeys, testAPIKey, APIKeyUpdate } from '@/api/settings'
import { cn } from '@/lib/utils'
import {
  CheckCircle,
  XCircle,
  Loader2,
  Eye,
  EyeOff,
  TestTube,
  Save,
} from 'lucide-react'

interface APIKeyInputProps {
  label: string
  description: string
  value: string
  onChange: (value: string) => void
  configured: boolean
  lastTested: string | null
  testSuccess: boolean | null
  onTest: () => void
  isTesting: boolean
  placeholder?: string
  type?: 'text' | 'password'
}

function APIKeyInput({
  label,
  description,
  value,
  onChange,
  configured,
  lastTested,
  testSuccess,
  onTest,
  isTesting,
  placeholder,
  type = 'password',
}: APIKeyInputProps) {
  const [showValue, setShowValue] = useState(false)

  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium">{label}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        <div className="flex items-center gap-2">
          {configured ? (
            <span className="flex items-center gap-1 text-sm text-green-500">
              <CheckCircle className="h-4 w-4" />
              Configured
            </span>
          ) : (
            <span className="flex items-center gap-1 text-sm text-muted-foreground">
              <XCircle className="h-4 w-4" />
              Not configured
            </span>
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <input
            type={showValue ? 'text' : type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={configured ? '••••••••••••••••' : placeholder}
            className="w-full px-3 py-2 border rounded-md bg-background pr-10"
          />
          {type === 'password' && (
            <button
              type="button"
              onClick={() => setShowValue(!showValue)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              {showValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          )}
        </div>
        <button
          onClick={onTest}
          disabled={isTesting || (!configured && !value)}
          className={cn(
            'px-3 py-2 rounded-md flex items-center gap-2 text-sm font-medium',
            'bg-secondary text-secondary-foreground hover:bg-secondary/80',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {isTesting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <TestTube className="h-4 w-4" />
          )}
          Test
        </button>
      </div>

      {lastTested && (
        <div
          className={cn(
            'text-sm flex items-center gap-1',
            testSuccess ? 'text-green-500' : 'text-red-500'
          )}
        >
          {testSuccess ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <XCircle className="h-4 w-4" />
          )}
          Last tested: {new Date(lastTested).toLocaleString()}
          {testSuccess ? ' - Success' : ' - Failed'}
        </div>
      )}
    </div>
  )
}

export default function Settings() {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<APIKeyUpdate>({})
  const [testingService, setTestingService] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ service: string; message: string; success: boolean } | null>(null)

  const { data: status, isLoading } = useQuery({
    queryKey: ['api-key-status'],
    queryFn: getAPIKeyStatus,
  })

  const updateMutation = useMutation({
    mutationFn: updateAPIKeys,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-key-status'] })
      setFormData({})
    },
  })

  const testMutation = useMutation({
    mutationFn: testAPIKey,
    onSuccess: (result) => {
      setTestResult({ service: result.service, message: result.message, success: result.success })
      queryClient.invalidateQueries({ queryKey: ['api-key-status'] })
    },
    onSettled: () => {
      setTestingService(null)
    },
  })

  const handleTest = (service: string) => {
    setTestingService(service)
    setTestResult(null)
    testMutation.mutate(service)
  }

  const handleSave = () => {
    if (Object.keys(formData).length > 0) {
      updateMutation.mutate(formData)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Configure API keys and integrations</p>
        </div>
        <button
          onClick={handleSave}
          disabled={Object.keys(formData).length === 0 || updateMutation.isPending}
          className={cn(
            'px-4 py-2 rounded-md flex items-center gap-2 font-medium',
            'bg-primary text-primary-foreground hover:bg-primary/90',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {updateMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Save Changes
        </button>
      </div>

      {testResult && (
        <div
          className={cn(
            'p-4 rounded-lg',
            testResult.success ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
          )}
        >
          <strong>{testResult.service}:</strong> {testResult.message}
        </div>
      )}

      {/* Market Data */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold border-b pb-2">Market Data APIs</h2>

        <APIKeyInput
          label="Polygon.io"
          description="Real-time and historical stock prices"
          value={formData.polygon_api_key || ''}
          onChange={(v) => setFormData({ ...formData, polygon_api_key: v })}
          configured={status?.polygon.configured || false}
          lastTested={status?.polygon.last_tested || null}
          testSuccess={status?.polygon.test_success || null}
          onTest={() => handleTest('polygon')}
          isTesting={testingService === 'polygon'}
          placeholder="Enter Polygon API key"
        />

        <APIKeyInput
          label="SEC API"
          description="SEC filings and insider transactions"
          value={formData.sec_api_key || ''}
          onChange={(v) => setFormData({ ...formData, sec_api_key: v })}
          configured={status?.sec_api.configured || false}
          lastTested={status?.sec_api.last_tested || null}
          testSuccess={status?.sec_api.test_success || null}
          onTest={() => handleTest('sec_api')}
          isTesting={testingService === 'sec_api'}
          placeholder="Enter SEC API key"
        />

        <APIKeyInput
          label="Benzinga"
          description="Financial news and sentiment"
          value={formData.benzinga_api_key || ''}
          onChange={(v) => setFormData({ ...formData, benzinga_api_key: v })}
          configured={status?.benzinga.configured || false}
          lastTested={status?.benzinga.last_tested || null}
          testSuccess={status?.benzinga.test_success || null}
          onTest={() => handleTest('benzinga')}
          isTesting={testingService === 'benzinga'}
          placeholder="Enter Benzinga API key"
        />
      </section>

      {/* Trading */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold border-b pb-2">Trading</h2>

        <div className="border rounded-lg p-4 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-medium">Alpaca</h3>
              <p className="text-sm text-muted-foreground">Stock trading broker</p>
            </div>
            <div className="flex items-center gap-2">
              {status?.alpaca.configured ? (
                <span className="flex items-center gap-1 text-sm text-green-500">
                  <CheckCircle className="h-4 w-4" />
                  Configured
                </span>
              ) : (
                <span className="flex items-center gap-1 text-sm text-muted-foreground">
                  <XCircle className="h-4 w-4" />
                  Not configured
                </span>
              )}
            </div>
          </div>

          <div className="grid gap-3">
            <div>
              <label className="text-sm text-muted-foreground">API Key</label>
              <input
                type="password"
                value={formData.alpaca_api_key || ''}
                onChange={(e) => setFormData({ ...formData, alpaca_api_key: e.target.value })}
                placeholder={status?.alpaca.configured ? '••••••••••••••••' : 'Enter Alpaca API key'}
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">API Secret</label>
              <input
                type="password"
                value={formData.alpaca_api_secret || ''}
                onChange={(e) => setFormData({ ...formData, alpaca_api_secret: e.target.value })}
                placeholder={status?.alpaca.configured ? '••••••••••••••••' : 'Enter Alpaca API secret'}
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="paper-trading"
                checked={formData.alpaca_paper_trading ?? status?.alpaca_paper_trading ?? true}
                onChange={(e) => setFormData({ ...formData, alpaca_paper_trading: e.target.checked })}
                className="h-4 w-4"
              />
              <label htmlFor="paper-trading" className="text-sm">
                Paper Trading Mode (recommended for testing)
              </label>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleTest('alpaca')}
              disabled={testingService === 'alpaca' || (!status?.alpaca.configured && !formData.alpaca_api_key)}
              className={cn(
                'px-3 py-2 rounded-md flex items-center gap-2 text-sm font-medium',
                'bg-secondary text-secondary-foreground hover:bg-secondary/80',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {testingService === 'alpaca' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <TestTube className="h-4 w-4" />
              )}
              Test Connection
            </button>
            {status?.alpaca.last_tested && (
              <span
                className={cn(
                  'text-sm flex items-center gap-1',
                  status.alpaca.test_success ? 'text-green-500' : 'text-red-500'
                )}
              >
                {status.alpaca.test_success ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                {status.alpaca.test_success ? 'Connected' : 'Failed'}
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Notifications */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold border-b pb-2">Notifications</h2>

        <APIKeyInput
          label="SendGrid"
          description="Email notifications via SendGrid"
          value={formData.sendgrid_api_key || ''}
          onChange={(v) => setFormData({ ...formData, sendgrid_api_key: v })}
          configured={status?.sendgrid.configured || false}
          lastTested={status?.sendgrid.last_tested || null}
          testSuccess={status?.sendgrid.test_success || null}
          onTest={() => handleTest('sendgrid')}
          isTesting={testingService === 'sendgrid'}
          placeholder="Enter SendGrid API key"
        />

        {/* SMTP */}
        <div className="border rounded-lg p-4 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-medium">SMTP</h3>
              <p className="text-sm text-muted-foreground">Email notifications via SMTP server</p>
            </div>
            <div className="flex items-center gap-2">
              {status?.smtp.configured ? (
                <span className="flex items-center gap-1 text-sm text-green-500">
                  <CheckCircle className="h-4 w-4" />
                  Configured
                </span>
              ) : (
                <span className="flex items-center gap-1 text-sm text-muted-foreground">
                  <XCircle className="h-4 w-4" />
                  Not configured
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-muted-foreground">SMTP Host</label>
              <input
                type="text"
                value={formData.smtp_host ?? status?.smtp_host ?? ''}
                onChange={(e) => setFormData({ ...formData, smtp_host: e.target.value })}
                placeholder="smtp.gmail.com"
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Port</label>
              <input
                type="text"
                value={formData.smtp_port ?? status?.smtp_port ?? ''}
                onChange={(e) => setFormData({ ...formData, smtp_port: e.target.value })}
                placeholder="587"
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Username</label>
              <input
                type="text"
                value={formData.smtp_username || ''}
                onChange={(e) => setFormData({ ...formData, smtp_username: e.target.value })}
                placeholder="your@email.com"
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Password</label>
              <input
                type="password"
                value={formData.smtp_password || ''}
                onChange={(e) => setFormData({ ...formData, smtp_password: e.target.value })}
                placeholder={status?.smtp.configured ? '••••••••••••••••' : 'App password'}
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">From Email</label>
              <input
                type="email"
                value={formData.smtp_from_email ?? status?.smtp_from_email ?? ''}
                onChange={(e) => setFormData({ ...formData, smtp_from_email: e.target.value })}
                placeholder="alerts@example.com"
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="smtp-tls"
                checked={formData.smtp_use_tls ?? status?.smtp_use_tls ?? true}
                onChange={(e) => setFormData({ ...formData, smtp_use_tls: e.target.checked })}
                className="h-4 w-4"
              />
              <label htmlFor="smtp-tls" className="text-sm">Use TLS</label>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleTest('smtp')}
              disabled={testingService === 'smtp' || (!status?.smtp.configured && !formData.smtp_host)}
              className={cn(
                'px-3 py-2 rounded-md flex items-center gap-2 text-sm font-medium',
                'bg-secondary text-secondary-foreground hover:bg-secondary/80',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {testingService === 'smtp' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <TestTube className="h-4 w-4" />
              )}
              Test Connection
            </button>
            {status?.smtp.last_tested && (
              <span
                className={cn(
                  'text-sm flex items-center gap-1',
                  status.smtp.test_success ? 'text-green-500' : 'text-red-500'
                )}
              >
                {status.smtp.test_success ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                {status.smtp.test_success ? 'Connected' : 'Failed'}
              </span>
            )}
          </div>
        </div>

        {/* Twilio */}
        <div className="border rounded-lg p-4 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-medium">Twilio</h3>
              <p className="text-sm text-muted-foreground">SMS notifications</p>
            </div>
            <div className="flex items-center gap-2">
              {status?.twilio.configured ? (
                <span className="flex items-center gap-1 text-sm text-green-500">
                  <CheckCircle className="h-4 w-4" />
                  Configured
                </span>
              ) : (
                <span className="flex items-center gap-1 text-sm text-muted-foreground">
                  <XCircle className="h-4 w-4" />
                  Not configured
                </span>
              )}
            </div>
          </div>

          <div className="grid gap-3">
            <div>
              <label className="text-sm text-muted-foreground">Account SID</label>
              <input
                type="password"
                value={formData.twilio_account_sid || ''}
                onChange={(e) => setFormData({ ...formData, twilio_account_sid: e.target.value })}
                placeholder={status?.twilio.configured ? '••••••••••••••••' : 'Enter Twilio Account SID'}
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Auth Token</label>
              <input
                type="password"
                value={formData.twilio_auth_token || ''}
                onChange={(e) => setFormData({ ...formData, twilio_auth_token: e.target.value })}
                placeholder={status?.twilio.configured ? '••••••••••••••••' : 'Enter Twilio Auth Token'}
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Phone Number</label>
              <input
                type="text"
                value={formData.twilio_phone_number || ''}
                onChange={(e) => setFormData({ ...formData, twilio_phone_number: e.target.value })}
                placeholder="+1234567890"
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleTest('twilio')}
              disabled={testingService === 'twilio' || (!status?.twilio.configured && !formData.twilio_account_sid)}
              className={cn(
                'px-3 py-2 rounded-md flex items-center gap-2 text-sm font-medium',
                'bg-secondary text-secondary-foreground hover:bg-secondary/80',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {testingService === 'twilio' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <TestTube className="h-4 w-4" />
              )}
              Test Connection
            </button>
            {status?.twilio.last_tested && (
              <span
                className={cn(
                  'text-sm flex items-center gap-1',
                  status.twilio.test_success ? 'text-green-500' : 'text-red-500'
                )}
              >
                {status.twilio.test_success ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                {status.twilio.test_success ? 'Connected' : 'Failed'}
              </span>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
