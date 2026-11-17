export interface CampaignItem {
  id: number
  name: string
  alias: string
}

export interface CampaignCreatePayload {
  name: string
  geo: string
  offer_id: number
  domain_id?: number
  group_id?: number
  source_id?: number
}
