import { useState } from "react"
import { Auth } from "@/entities/auth/api"
import { ApiError } from "@/shared/api/client"
import { Button } from "@/shared/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"

export function LoginForm({ onLogin }: { onLogin: () => void }) {
  const [baseUrl, setBaseUrl] = useState("https://tlgk.host")
  const [login, setLogin] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      await Auth.login(baseUrl, login, password)

      onLogin()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Connection failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Connect to Keitaro</CardTitle>

          <CardDescription>Tracker URL and admin panel credentials</CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="base_url">Tracker URL</Label>

              <Input
                id="base_url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://tracker.example.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="login">Login</Label>

              <Input
                id="login"
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                autoComplete="username"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>

              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Connecting…" : "Connect"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
