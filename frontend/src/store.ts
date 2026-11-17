import { create } from "zustand"
import { persist } from "zustand/middleware"

interface UiState {
  activeTab: string
  campaignId: string
  campaignLabel: string
  setActiveTab: (tab: string) => void
  setCampaign: (id: string, label: string) => void
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      activeTab: "create",
      campaignId: "",
      campaignLabel: "",
      setActiveTab: (tab) => set({ activeTab: tab }),
      setCampaign: (id, label) => set({ campaignId: id, campaignLabel: label }),
    }),
    { name: "keitaro-ui" }
  )
)
