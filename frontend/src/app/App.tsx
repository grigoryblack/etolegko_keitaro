import { useEffect, useState } from "react"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import { GuestOnly, RequireAuth } from "@/app/guards"
import { Auth } from "@/entities/auth/api"
import { LoginPage } from "@/pages/login/LoginPage"
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

  return (
    <BrowserRouter>
      <Toaster richColors position="top-right" />

      <Routes>
        <Route
          path="/login"
          element={
            <GuestOnly connected={connected}>
              <LoginPage onLogin={() => setConnected(true)} />
            </GuestOnly>
          }
        />

        <Route
          path="/"
          element={
            <RequireAuth connected={connected}>
              <WorkspacePage baseUrl={baseUrl} onLogout={() => setConnected(false)} />
            </RequireAuth>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
