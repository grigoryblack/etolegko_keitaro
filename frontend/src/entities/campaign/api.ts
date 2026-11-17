import { api, post } from "@/shared/api/client"
import type { LocalStream } from "@/entities/stream/types"
import type { CampaignCreatePayload, CampaignItem } from "./types"

export const Campaigns = {
  list: () => api<CampaignItem[]>("/campaigns"),
  search: (q: string) => api<CampaignItem[]>(`/campaigns/search?query=${encodeURIComponent(q)}`),
  create: (p: CampaignCreatePayload) =>
    post<{ campaign: { id: number }; streams: Array<{ id: number }> }>("/campaigns", p),
  fetchStreams: (id: number) => post<LocalStream[]>(`/campaigns/${id}/fetch_streams`),
  localStreams: (id: number) => api<LocalStream[]>(`/campaigns/${id}/streams`),
}
