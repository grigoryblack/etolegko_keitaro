import { useEffect, useState } from "react"
import { Campaigns, Refs, type RefItem } from "@/api"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const NONE = "__none__"

function RefSelect({
  label, items, value, onChange, optional = true,
}: { label: string; items: RefItem[]; value: string; onChange: (v: string) => void; optional?: boolean }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger><SelectValue placeholder={`Select ${label.toLowerCase()}`} /></SelectTrigger>
        <SelectContent>
          {optional && <SelectItem value={NONE}>— none —</SelectItem>}
          {items.map((i) => <SelectItem key={i.id} value={String(i.id)}>{`#${i.id} — ${i.name}`}</SelectItem>)}
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
    Refs.offers().then(setOffers).catch(() => {})
    Refs.domains().then(setDomains).catch(() => {})
    Refs.groups().then(setGroups).catch(() => {})
    Refs.sources().then(setSources).catch(() => setSourcesDenied(true))
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
          ? (sourceManual ? Number(sourceManual) : undefined)
          : sourceId !== NONE ? Number(sourceId) : undefined,
      }
      const res = await Campaigns.create(payload)
      toast.success(`Campaign created! Keitaro ID: ${res.campaign.id}, streams: ${res.streams.map((s) => s.id).join(", ")}`)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create campaign</CardTitle>
        <CardDescription>
          Creates a campaign with two flows: geo → Google redirect, everyone else → selected offer
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid max-w-md gap-4">
          <div className="space-y-2">
            <Label htmlFor="cname">Campaign name</Label>
            <Input id="cname" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="geo">Geo (ISO alpha-2)</Label>
            <Input id="geo" value={geo} onChange={(e) => setGeo(e.target.value)} maxLength={2} placeholder="NL" required className="w-24" />
          </div>
          <RefSelect label="Offer" items={offers} value={offerId} onChange={setOfferId} optional={false} />
          <RefSelect label="Domain" items={domains} value={domainId} onChange={setDomainId} />
          <RefSelect label="Group" items={groups} value={groupId} onChange={setGroupId} />
          {sourcesDenied ? (
            <div className="space-y-2">
              <Label>Traffic source ID</Label>
              <Input value={sourceManual} onChange={(e) => setSourceManual(e.target.value)} placeholder="ID (list unavailable)" type="number" />
            </div>
          ) : (
            <RefSelect label="Traffic source" items={sources} value={sourceId} onChange={setSourceId} />
          )}
          <Button type="submit" disabled={loading || !offerId} className="w-fit">
            {loading ? "Creating…" : "Create campaign"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
