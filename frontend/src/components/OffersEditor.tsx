import { useEffect, useRef, useState } from "react"
import { Campaigns, Refs, Streams, type LocalStream, type RefItem } from "@/api"
import { useUiStore } from "@/store"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Pin, RotateCcw, Trash2, Undo2, Upload } from "lucide-react"

function StreamCard({
  stream, onChange, onError,
}: { stream: LocalStream; onChange: (s: LocalStream) => void; onError: (m: string) => void }) {
  const [offerInput, setOfferInput] = useState("")
  const [suggestions, setSuggestions] = useState<RefItem[]>([])
  const [busy, setBusy] = useState(false)
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const run = async (fn: () => Promise<LocalStream>) => {
    setBusy(true)
    try {
      onChange(await fn())
    } catch (e) {
      onError(e instanceof Error ? e.message : "Error")
    } finally {
      setBusy(false)
    }
  }

  const search = (q: string) => {
    setOfferInput(q)
    clearTimeout(debounce.current)
    if (!q.trim()) return setSuggestions([])
    debounce.current = setTimeout(async () => {
      try {
        setSuggestions(await Refs.offerSearch(q))
      } catch { /* ignore */ }
    }, 200)
  }

  const active = stream.offers.filter((o) => o.status === "active")
  const removed = stream.offers.filter((o) => o.status === "removed")
  const label = (o: { offer_id: number; offer_name: string | null }) =>
    o.offer_name ? `#${o.offer_id} — ${o.offer_name}` : `#${o.offer_id}`

  return (
    <Card className={stream.dirty ? "border-yellow-400 bg-yellow-50" : ""}>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between gap-2">
          <div>
            <span className="font-semibold">#{stream.keitaro_id} — {stream.name}</span>
            {stream.dirty && <Badge className="ml-2 bg-yellow-400 text-yellow-900 hover:bg-yellow-400">unpublished</Badge>}
            <p className="text-xs text-muted-foreground">
              type: {stream.type ?? "—"} · schema: {stream.schema ?? "—"} · state: {stream.state ?? "—"}
            </p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" disabled={!stream.dirty || busy} onClick={() => run(() => Streams.push(stream.id))}>
              <Upload className="mr-1 h-4 w-4" />Push to KTM
            </Button>
            <Button size="sm" variant="secondary" disabled={!stream.dirty || busy} onClick={() => run(() => Streams.cancel(stream.id))}>
              <Undo2 className="mr-1 h-4 w-4" />Cancel
            </Button>
          </div>
        </div>

        <Table className="mt-3">
          <TableHeader>
            <TableRow>
              <TableHead>Offer</TableHead>
              <TableHead className="w-20">Weight</TableHead>
              <TableHead className="w-20">Pin</TableHead>
              <TableHead className="w-32" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {active.length === 0 && removed.length === 0 && (
              <TableRow><TableCell colSpan={4} className="text-muted-foreground">Flow without offers</TableCell></TableRow>
            )}
            {active.map((o) => (
              <TableRow key={o.id}>
                <TableCell>{label(o)}</TableCell>
                <TableCell className="font-semibold tabular-nums">{o.share}%</TableCell>
                <TableCell>
                  <Button size="sm" variant={o.pinned ? "default" : "outline"} disabled={busy}
                    onClick={() => run(() => Streams.togglePin(stream.id, o.offer_id))}>
                    <Pin className="h-4 w-4" />
                  </Button>
                </TableCell>
                <TableCell>
                  <Button size="sm" variant="destructive" disabled={busy}
                    onClick={() => run(() => Streams.removeOffer(stream.id, o.offer_id))}>
                    <Trash2 className="mr-1 h-4 w-4" />Remove
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {removed.map((o) => (
              <TableRow key={o.id} className="bg-muted text-muted-foreground">
                <TableCell>{label(o)} <Badge variant="secondary" className="ml-2">Removed</Badge></TableCell>
                <TableCell className="tabular-nums">{o.share}%</TableCell>
                <TableCell />
                <TableCell>
                  <Button size="sm" variant="outline" disabled={busy}
                    onClick={() => run(() => Streams.restoreOffer(stream.id, o.offer_id))}>
                    <RotateCcw className="mr-1 h-4 w-4" />Bring back
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="relative mt-3 flex max-w-md gap-2">
          <div className="relative flex-1">
            <Input placeholder="Offer ID or name" value={offerInput} onChange={(e) => search(e.target.value)} />
            {suggestions.length > 0 && offerInput && (
              <div className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-md border bg-popover shadow-md">
                {suggestions.slice(0, 15).map((o) => (
                  <button key={o.id} type="button" className="block w-full px-3 py-1.5 text-left text-sm hover:bg-accent"
                    onClick={() => { setOfferInput(String(o.id)); setSuggestions([]) }}>
                    #{o.id} — {o.name}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button size="sm" disabled={busy || !offerInput.trim()}
            onClick={() => { setSuggestions([]); run(() => Streams.addOffer(stream.id, Number(offerInput.trim()))) }}>
            Add offer
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

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
        setSuggestions(await Refs.campaignSearch(q))
      } catch { /* ignore */ }
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
    setCampaign(cid, campaignInput || campaignLabel)
    setStreams([])
    if (!cid) return
    try {
      setStreams(await Campaigns.localStreams(Number(cid)))
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error")
    }
  }

  const fetchStreams = async () => {
    if (!campaignId) return toast.error("Select a campaign")
    setBusy(true)
    try {
      setStreams(await Campaigns.fetchStreams(Number(campaignId)))
      toast.success("Streams synced with Keitaro")
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error")
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
          <Label>Campaign</Label>
          <Input
            placeholder="ID, name or alias"
            value={campaignInput}
            onChange={(e) => search(e.target.value)}
            onBlur={() => setTimeout(() => setSuggestions([]), 150)}
          />
          {suggestions.length > 0 && (
            <div className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-md border bg-popover shadow-md">
              {suggestions.slice(0, 20).map((c) => (
                <button key={c.id} type="button"
                  className="block w-full px-3 py-1.5 text-left text-sm hover:bg-accent"
                  onMouseDown={(e) => { e.preventDefault(); pickCampaign(c) }}>
                  #{c.id} — {c.name}
                </button>
              ))}
            </div>
          )}
        </div>
        <Button onClick={fetchStreams} disabled={busy}>Fetch streams again</Button>
      </div>

      {streams.length === 0 && campaignId && (
        <p className="text-sm text-muted-foreground">No local streams — press «Fetch streams again»</p>
      )}
      {streams.map((s) => (
        <StreamCard key={s.id} stream={s} onChange={updateStream}
          onError={(m) => toast.error(m)} />
      ))}
    </div>
  )
}
