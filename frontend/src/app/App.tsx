import { useEffect, useState } from "react"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

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
            connected ? (
              <Navigate to="/" replace />
            ) : (
              <LoginPage onLogin={() => setConnected(true)} />
            )
          }
        />

        <Route
          path="/"
          element={
            connected ? (
              <WorkspacePage baseUrl={baseUrl} onLogout={() => setConnected(false)} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
