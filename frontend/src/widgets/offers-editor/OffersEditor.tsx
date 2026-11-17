import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { Campaigns } from "@/entities/campaign/api"
import type { LocalStream } from "@/entities/stream/types"
import { useUiStore } from "@/shared/store/ui"
import { Button } from "@/shared/ui/button"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"
import { StreamCard } from "@/widgets/stream-card/StreamCard"

export function OffersEditor() {
  const campaignId = useUiStore((s) => s.campaignId)
  const campaignLabel = useUiStore((s) => s.campaignLabel)
  const setCampaign = useUiStore((s) => s.setCampaign)
  const [campaignInput, setCampaignInput] = useState(campaignLabel)
  const [suggestions, setSuggestions] = useState<Array<{ id: number; name: string }>>([])
  const [streams, setStreams] = useState<LocalStream[]>([])
  const [busy, setBusy] = useState(false)
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    if (campaignId) loadLocal(campaignId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const search = (q: string) => {
    setCampaignInput(q)
    setCampaign("", "")
    clearTimeout(debounce.current)
    if (!q.trim()) return setSuggestions([])
    debounce.current = setTimeout(async () => {
      try {
        setSuggestions(await Campaigns.search(q))
      } catch {
        /* ignore */
      }
    }, 200)
  }

  const pickCampaign = (c: { id: number; name: string }) => {
    const label = `#${c.id} — ${c.name}`
    setCampaignInput(label)
    setSuggestions([])
    setCampaign(String(c.id), label)
    loadLocal(String(c.id))
  }

  const loadLocal = async (cid: string) => {
    setStreams([])
    if (!cid) return
    try {
      setStreams(await Campaigns.localStreams(Number(cid)))
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Ошибка")
    }
  }

  const fetchStreams = async () => {
    if (!campaignId) return toast.error("Выберите кампанию")
    setBusy(true)
    try {
      setStreams(await Campaigns.fetchStreams(Number(campaignId)))
      toast.success("Потоки синхронизированы с Keitaro")
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Ошибка")
    } finally {
      setBusy(false)
    }
  }

  const updateStream = (s: LocalStream) =>
    setStreams((prev) => prev.map((x) => (x.id === s.id ? s : x)))

  return (
    <div className="space-y-4">
      <div className="flex max-w-xl items-end gap-2">
        <div className="relative flex-1 space-y-2">
          <Label>Кампания</Label>
          <Input
            placeholder="ID, название или алиас"
            value={campaignInput}
            onChange={(e) => search(e.target.value)}
            onBlur={() => setTimeout(() => setSuggestions([]), 150)}
          />
          {suggestions.length > 0 && (
            <div className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-md border bg-popover shadow-md">
              {suggestions.slice(0, 20).map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className="block w-full px-3 py-1.5 text-left text-sm hover:bg-accent"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    pickCampaign(c)
                  }}
                >
                  #{c.id} — {c.name}
                </button>
              ))}
            </div>
          )}
        </div>
        <Button onClick={fetchStreams} disabled={busy}>
          Загрузить потоки заново
        </Button>
      </div>

      {streams.length === 0 && campaignId && (
        <p className="text-sm text-muted-foreground">
          Локальных потоков нет — нажмите «Загрузить потоки заново»
        </p>
      )}
      {streams.map((s) => (
        <StreamCard key={s.id} stream={s} onChange={updateStream} />
      ))}
    </div>
  )
}
