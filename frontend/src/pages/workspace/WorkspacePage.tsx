import { Auth } from "@/entities/auth/api"
import { useUiStore } from "@/shared/store/ui"
import { Button } from "@/shared/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs"
import { CampaignCreator } from "@/widgets/campaign-creator/CampaignCreator"
import { OffersEditor } from "@/widgets/offers-editor/OffersEditor"

export function WorkspacePage({ baseUrl, onLogout }: { baseUrl: string; onLogout: () => void }) {
  const activeTab = useUiStore((s) => s.activeTab)
  const setActiveTab = useUiStore((s) => s.setActiveTab)

  return (
    <div className="min-h-screen bg-muted/40">
      <header className="flex items-center justify-between border-b bg-background px-6 py-3">
        <h1 className="text-lg font-semibold">Keitaro Campaign Manager</h1>

        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <span>{baseUrl}</span>

          <Button size="sm" variant="outline" onClick={() => Auth.logout().finally(onLogout)}>
            Отключиться
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="create">Создание кампании</TabsTrigger>

            <TabsTrigger value="edit">Редактор офферов</TabsTrigger>
          </TabsList>

          <TabsContent value="create" className="mt-4">
            <CampaignCreator />
          </TabsContent>
          <TabsContent value="edit" className="mt-4">
            <OffersEditor />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
