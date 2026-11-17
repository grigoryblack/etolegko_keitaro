export interface RefItem {
  id: number
  name: string
}

export interface StreamOffer {
  id: number
  offer_id: number
  offer_name: string | null
  share: number
  pinned: boolean
  status: "active" | "removed"
}

export interface LocalStream {
  id: number
  keitaro_id: number
  campaign_id: number
  name: string
  type: string | null
  schema: string | null
  state: string | null
  dirty: boolean
  offers: StreamOffer[]
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data?.detail
    let msg: string
    if (Array.isArray(detail)) {
      // pydantic validation errors: [{loc, msg}, ...]
      msg = detail.map((e) => `${(e.loc ?? []).join(".")}: ${e.msg}`).join("; ")
    } else if (typeof detail === "string") {
      msg = detail
    } else {
      msg = detail?.error ?? JSON.stringify(detail) ?? res.statusText
    }
    throw new ApiError(res.status, String(msg))
  }
  return data as T
}

const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined })

export const Auth = {
  status: () => api<{ connected: boolean; base_url: string | null }>("/auth/status"),
  login: (base_url: string, login: string, password: string) =>
    post("/auth/login", { base_url, login, password }),
  logout: () => post("/auth/logout"),
}

export const Refs = {
  offers: () => api<RefItem[]>("/offers"),
  offerSearch: (q: string) => api<RefItem[]>(`/offers/search?query=${encodeURIComponent(q)}`),
  domains: () => api<RefItem[]>("/domains"),
  groups: () => api<RefItem[]>("/groups"),
  sources: () => api<RefItem[]>("/sources"),
  campaigns: () => api<Array<{ id: number; name: string; alias: string }>>("/campaigns"),
}

export interface CampaignCreatePayload {
  name: string
  geo: string
  offer_id: number
  domain_id?: number
  group_id?: number
  source_id?: number
}

export const Campaigns = {
  create: (p: CampaignCreatePayload) =>
    post<{ campaign: { id: number }; streams: Array<{ id: number }> }>("/campaigns", p),
  fetchStreams: (id: number) => post<LocalStream[]>(`/campaigns/${id}/fetch_streams`),
  localStreams: (id: number) => api<LocalStream[]>(`/campaigns/${id}/streams`),
}

export const Streams = {
  addOffer: (sid: number, offer_id: number) => post<LocalStream>(`/streams/${sid}/offers`, { offer_id }),
  removeOffer: (sid: number, oid: number) => post<LocalStream>(`/streams/${sid}/offers/${oid}/remove`),
  restoreOffer: (sid: number, oid: number) => post<LocalStream>(`/streams/${sid}/offers/${oid}/restore`),
  togglePin: (sid: number, oid: number) => post<LocalStream>(`/streams/${sid}/offers/${oid}/pin`),
  push: (sid: number) => post<LocalStream>(`/streams/${sid}/push`),
  cancel: (sid: number) => post<LocalStream>(`/streams/${sid}/cancel`),
}
