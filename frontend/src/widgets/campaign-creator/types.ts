import type { RefItem } from "@/shared/types/refs"

export interface RefSelectProps {
  label: string
  items: RefItem[]
  value: string
  onChange: (v: string) => void
  optional?: boolean
  placeholder: string
}
