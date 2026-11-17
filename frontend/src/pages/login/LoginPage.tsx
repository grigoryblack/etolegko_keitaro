import { LoginForm } from "@/features/auth/LoginForm"
import type { LoginPageProps } from "./types"

export function LoginPage({ onLogin }: LoginPageProps) {
  return <LoginForm onLogin={onLogin} />
}
