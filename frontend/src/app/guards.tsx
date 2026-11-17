import { Navigate } from "react-router-dom"

import type { GuardProps } from "./types"

export function RequireAuth({ connected, children }: GuardProps) {
  return connected ? children : <Navigate to="/login" replace />
}

export function GuestOnly({ connected, children }: GuardProps) {
  return connected ? <Navigate to="/" replace /> : children
}
