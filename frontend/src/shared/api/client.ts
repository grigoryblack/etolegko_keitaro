export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data?.detail
    let msg: string
    if (Array.isArray(detail)) {
      // pydantic validation errors: [{loc, msg}, ...]
      msg = detail.map((e) => `${(e.loc ?? []).join(".")}: ${e.msg}`).join("; ")
    } else if (typeof detail === "string") {
      msg = detail
    } else {
      msg = detail?.error ?? JSON.stringify(detail) ?? res.statusText
    }
    throw new ApiError(res.status, String(msg))
  }
  return data as T
}

export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined })
