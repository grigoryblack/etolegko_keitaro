import { useEffect, useState } from "react"
import { Campaigns } from "@/entities/campaign/api"
import { Offers } from "@/entities/offer/api"
import { Refs } from "@/entities/reference/api"
import type { RefItem } from "@/shared/types/refs"
import { toast } from "sonner"
import { Button } from "@/shared/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select"

const NONE = "__none__"

function RefSelect({
  label,
  items,
  value,
  onChange,
  optional = true,
  placeholder,
}: {
  label: string
  items: RefItem[]
  value: string
  onChange: (v: string) => void
  optional?: boolean
  placeholder: string
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>

      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>

        <SelectContent>
          {optional && <SelectItem value={NONE}>— не выбрано —</SelectItem>}
          {items.map((i) => (
            <SelectItem key={i.id} value={String(i.id)}>{`#${i.id} — ${i.name}`}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

export function CampaignCreator() {
  const [offers, setOffers] = useState<RefItem[]>([])
  const [domains, setDomains] = useState<RefItem[]>([])
  const [groups, setGroups] = useState<RefItem[]>([])
  const [sources, setSources] = useState<RefItem[]>([])
  const [sourcesDenied, setSourcesDenied] = useState(false)

  const [name, setName] = useState("")
  const [geo, setGeo] = useState("")
  const [offerId, setOfferId] = useState("")
  const [domainId, setDomainId] = useState(NONE)
  const [groupId, setGroupId] = useState(NONE)
  const [sourceId, setSourceId] = useState(NONE)
  const [sourceManual, setSourceManual] = useState("")

  const [loading, setLoading] = useState(false)

  useEffect(() => {
    Offers.list()
      .then(setOffers)
      .catch(() => {})
    Refs.domains()
      .then(setDomains)
      .catch(() => {})
    Refs.groups()
      .then(setGroups)
      .catch(() => {})
    Refs.sources()
      .then(setSources)
      .catch(() => setSourcesDenied(true))
  }, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        name: name.trim(),
        geo: geo.trim().toUpperCase(),
        offer_id: Number(offerId),
        domain_id: domainId !== NONE ? Number(domainId) : undefined,
        group_id: groupId !== NONE ? Number(groupId) : undefined,
        source_id: sourcesDenied
          ? sourceManual
            ? Number(sourceManual)
            : undefined
          : sourceId !== NONE
            ? Number(sourceId)
            : undefined,
      }

      const res = await Campaigns.create(payload)
      toast.success(
        `Кампания создана! ID в Keitaro: ${res.campaign.id}, потоки: ${res.streams.map((s) => s.id).join(", ")}`
      )
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Ошибка")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Создание кампании</CardTitle>

        <CardDescription>
          Создаёт кампанию с двумя потоками: гео → редирект на Google, остальные → выбранный оффер
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid max-w-md gap-4">
          <div className="space-y-2">
            <Label htmlFor="cname">Название кампании</Label>

            <Input id="cname" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>

          <div className="space-y-2">
            <Label htmlFor="geo">Гео (код страны, 2 буквы)</Label>

            <Input
              id="geo"
              value={geo}
              onChange={(e) => setGeo(e.target.value)}
              maxLength={2}
              placeholder="NL"
              required
              className="w-24"
            />
          </div>

          <RefSelect
            label="Оффер"
            placeholder="Выберите оффер"
            items={offers}
            value={offerId}
            onChange={setOfferId}
            optional={false}
          />

          <RefSelect
            label="Домен"
            placeholder="Выберите домен"
            items={domains}
            value={domainId}
            onChange={setDomainId}
          />

          <RefSelect
            label="Группа"
            placeholder="Выберите группу"
            items={groups}
            value={groupId}
            onChange={setGroupId}
          />

          {sourcesDenied ? (
            <div className="space-y-2">
              <Label>ID источника трафика</Label>

              <Input
                value={sourceManual}
                onChange={(e) => setSourceManual(e.target.value)}
                placeholder="ID (список недоступен)"
                type="number"
              />
            </div>
          ) : (
            <RefSelect
              label="Источник трафика"
              placeholder="Выберите источник"
              items={sources}
              value={sourceId}
              onChange={setSourceId}
            />
          )}
          <Button type="submit" disabled={loading || !offerId} className="w-fit">
            {loading ? "Создание…" : "Создать кампанию"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
