import { useEffect, useState } from "react"
import { Auth } from "@/api"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LoginForm } from "@/components/LoginForm"
import { CampaignCreator } from "@/components/CampaignCreator"
import { OffersEditor } from "@/components/OffersEditor"

export default function App() {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [baseUrl, setBaseUrl] = useState("")

  const check = () =>
    Auth.status()
      .then((s) => { setConnected(s.connected); setBaseUrl(s.base_url ?? "") })
      .catch(() => setConnected(false))

  useEffect(() => { check() }, [])

  if (connected === null) return null
  if (!connected) return <LoginForm onLogin={() => setConnected(true)} />

  return (
    <div className="min-h-screen bg-muted/40">
      <header className="flex items-center justify-between border-b bg-background px-6 py-3">
        <h1 className="text-lg font-semibold">Keitaro Campaign Manager</h1>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <span>{baseUrl}</span>
          <Button size="sm" variant="outline" onClick={() => Auth.logout().finally(() => setConnected(false))}>
            Disconnect
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-5xl p-6">
        <Tabs defaultValue="create">
          <TabsList>
            <TabsTrigger value="create">Create campaign</TabsTrigger>
            <TabsTrigger value="edit">Offers editor</TabsTrigger>
          </TabsList>
          <TabsContent value="create" className="mt-4"><CampaignCreator /></TabsContent>
          <TabsContent value="edit" className="mt-4"><OffersEditor /></TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
