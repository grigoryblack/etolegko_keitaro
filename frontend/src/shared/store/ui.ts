import { create, type StateCreator } from "zustand"
import { persist } from "zustand/middleware"

interface UiState {
  activeTab: string
  campaignId: string
  campaignLabel: string
  setActiveTab: (tab: string) => void
  setCampaign: (id: string, label: string) => void
}

const creator: StateCreator<UiState> = (set) => ({
  activeTab: "create",
  campaignId: "",
  campaignLabel: "",
  setActiveTab: (tab) => set({ activeTab: tab }),
  setCampaign: (id, label) => set({ campaignId: id, campaignLabel: label }),
})

export const useUiStore = create<UiState>()(persist(creator, { name: "keitaro-ui" }))
