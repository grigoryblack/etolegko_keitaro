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
