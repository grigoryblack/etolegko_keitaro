import { api } from "@/shared/api/client"
import type { RefItem } from "@/shared/types/refs"

export const Offers = {
  list: () => api<RefItem[]>("/offers"),
  search: (q: string) => api<RefItem[]>(`/offers/search?query=${encodeURIComponent(q)}`),
}
