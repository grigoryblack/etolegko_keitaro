import { useRef, useState } from "react"
import { toast } from "sonner"
import { Pin, RotateCcw, Trash2, Undo2, Upload } from "lucide-react"

import { Offers } from "@/entities/offer/api"
import { Streams } from "@/entities/stream/api"
import type { LocalStream } from "@/entities/stream/types"
import type { RefItem } from "@/shared/types/refs"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import { Card, CardContent } from "@/shared/ui/card"
import { Input } from "@/shared/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table"

export function StreamCard({
  stream,
  onChange,
}: {
  stream: LocalStream
  onChange: (s: LocalStream) => void
}) {
  const [offerInput, setOfferInput] = useState("")
  const [suggestions, setSuggestions] = useState<RefItem[]>([])
  const [busy, setBusy] = useState(false)
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const run = async (fn: () => Promise<LocalStream>) => {
    setBusy(true)
    try {
      onChange(await fn())
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Ошибка")
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
        setSuggestions(await Offers.search(q))
      } catch {
        /* ignore */
      }
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
            <span className="font-semibold">
              #{stream.keitaro_id} — {stream.name}
            </span>
            {stream.dirty && (
              <Badge className="ml-2 bg-yellow-400 text-yellow-900 hover:bg-yellow-400">
                не опубликовано
              </Badge>
            )}
            <p className="text-xs text-muted-foreground">
              тип: {stream.type ?? "—"} · схема: {stream.schema ?? "—"} · состояние:{" "}
              {stream.state ?? "—"}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              disabled={!stream.dirty || busy}
              onClick={() => run(() => Streams.push(stream.id))}
            >
              <Upload className="mr-1 h-4 w-4" />
              Push to KTM
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={!stream.dirty || busy}
              onClick={() => run(() => Streams.cancel(stream.id))}
            >
              <Undo2 className="mr-1 h-4 w-4" />
              Отменить
            </Button>
          </div>
        </div>

        <Table className="mt-3">
          <TableHeader>
            <TableRow>
              <TableHead>Оффер</TableHead>
              <TableHead className="w-20">Вес</TableHead>
              <TableHead className="w-20">Pin</TableHead>
              <TableHead className="w-32" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {active.length === 0 && removed.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-muted-foreground">
                  Поток без офферов
                </TableCell>
              </TableRow>
            )}
            {active.map((o) => (
              <TableRow key={o.id}>
                <TableCell>{label(o)}</TableCell>
                <TableCell className="font-semibold tabular-nums">{o.share}%</TableCell>
                <TableCell>
                  <Button
                    size="sm"
                    variant={o.pinned ? "default" : "outline"}
                    disabled={busy}
                    onClick={() => run(() => Streams.togglePin(stream.id, o.offer_id))}
                  >
                    <Pin className="h-4 w-4" />
                  </Button>
                </TableCell>
                <TableCell>
                  <Button
                    size="sm"
                    variant="destructive"
                    disabled={busy}
                    onClick={() => run(() => Streams.removeOffer(stream.id, o.offer_id))}
                  >
                    <Trash2 className="mr-1 h-4 w-4" />
                    Удалить
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {removed.map((o) => (
              <TableRow key={o.id} className="bg-muted text-muted-foreground">
                <TableCell>
                  {label(o)}{" "}
                  <Badge variant="secondary" className="ml-2">
                    Удалён
                  </Badge>
                </TableCell>
                <TableCell className="tabular-nums">{o.share}%</TableCell>
                <TableCell />
                <TableCell>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy}
                    onClick={() => run(() => Streams.restoreOffer(stream.id, o.offer_id))}
                  >
                    <RotateCcw className="mr-1 h-4 w-4" />
                    Вернуть
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="relative mt-3 flex max-w-md gap-2">
          <div className="relative flex-1">
            <Input
              placeholder="ID или название оффера"
              value={offerInput}
              onChange={(e) => search(e.target.value)}
            />
            {suggestions.length > 0 && offerInput && (
              <div className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-md border bg-popover shadow-md">
                {suggestions.slice(0, 15).map((o) => (
                  <button
                    key={o.id}
                    type="button"
                    className="block w-full px-3 py-1.5 text-left text-sm hover:bg-accent"
                    onClick={() => {
                      setOfferInput(String(o.id))
                      setSuggestions([])
                    }}
                  >
                    #{o.id} — {o.name}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button
            size="sm"
            disabled={busy || !offerInput.trim()}
            onClick={() => {
              setSuggestions([])
              run(() => Streams.addOffer(stream.id, Number(offerInput.trim())))
            }}
          >
            Добавить оффер
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
