import { post } from "@/shared/api/client"
import type { LocalStream } from "./types"

export const Streams = {
  addOffer: (sid: number, offer_id: number) =>
    post<LocalStream>(`/streams/${sid}/offers`, { offer_id }),
  removeOffer: (sid: number, oid: number) =>
    post<LocalStream>(`/streams/${sid}/offers/${oid}/remove`),
  restoreOffer: (sid: number, oid: number) =>
    post<LocalStream>(`/streams/${sid}/offers/${oid}/restore`),
  togglePin: (sid: number, oid: number) => post<LocalStream>(`/streams/${sid}/offers/${oid}/pin`),
  push: (sid: number) => post<LocalStream>(`/streams/${sid}/push`),
  cancel: (sid: number) => post<LocalStream>(`/streams/${sid}/cancel`),
}
