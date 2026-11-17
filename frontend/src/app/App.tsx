import { useEffect, useState } from "react"

import { Auth } from "@/entities/auth/api"
import { LoginForm } from "@/features/auth/LoginForm"
import { WorkspacePage } from "@/pages/workspace/WorkspacePage"
import { Toaster } from "@/shared/ui/sonner"

export default function App() {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [baseUrl, setBaseUrl] = useState("")

  useEffect(() => {
    Auth.status()
      .then((s) => {
        setConnected(s.connected)
        setBaseUrl(s.base_url ?? "")
      })
      .catch(() => setConnected(false))
  }, [])

  if (connected === null) return null

  if (!connected) {
    return (
      <>
        <Toaster richColors position="top-right" />

        <LoginForm onLogin={() => setConnected(true)} />
      </>
    )
  }

  return (
    <>
      <Toaster richColors position="top-right" />

      <WorkspacePage baseUrl={baseUrl} onLogout={() => setConnected(false)} />
    </>
  )
}
