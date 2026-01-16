import { useAuthStore } from '@/store/authSlice'

export default function Settings() {
  const { user } = useAuthStore()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Manage your account and preferences</p>
      </div>

      <div className="max-w-2xl space-y-6">
        {/* Profile */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Profile</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-3 py-2 border rounded-md bg-muted"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Full Name</label>
              <input
                type="text"
                defaultValue={user?.full_name || ''}
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Notifications</h2>
          <p className="text-muted-foreground">
            Configure your alert preferences for trading signals.
          </p>
        </div>

        {/* Broker Connection */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Broker Connection</h2>
          <p className="text-muted-foreground mb-4">
            Connect your broker account to enable semi-automated trading.
          </p>
          <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
            Connect Alpaca
          </button>
        </div>
      </div>
    </div>
  )
}
