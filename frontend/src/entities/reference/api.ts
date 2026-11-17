import { api } from "@/shared/api/client"
import type { RefItem } from "@/shared/types/refs"

export const Refs = {
  domains: () => api<RefItem[]>("/domains"),
  groups: () => api<RefItem[]>("/groups"),
  sources: () => api<RefItem[]>("/sources"),
}
