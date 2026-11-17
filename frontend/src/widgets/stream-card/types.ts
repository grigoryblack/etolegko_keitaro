import type { LocalStream } from "@/entities/stream/types"

export interface StreamCardProps {
  stream: LocalStream
  onChange: (s: LocalStream) => void
}
