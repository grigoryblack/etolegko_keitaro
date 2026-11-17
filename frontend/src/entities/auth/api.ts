import { api, post } from "@/shared/api/client"

export const Auth = {
  status: () => api<{ connected: boolean; base_url: string | null }>("/auth/status"),
  login: (base_url: string, login: string, password: string) =>
    post("/auth/login", { base_url, login, password }),
  logout: () => post("/auth/logout"),
}
