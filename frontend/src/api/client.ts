const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000'

const API_KEY = import.meta.env.VITE_API_KEY ?? ''

interface ApiErrorBody {
  detail?: string
}

export async function fetchApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')

  if (API_KEY) {
    headers.set('X-API-Key', API_KEY)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let message = `HTTP ${response.status}`
    try {
      const body = (await response.json()) as ApiErrorBody
      if (body.detail) {
        message = body.detail
      }
    } catch {
      // Ignore JSON parse failures and keep fallback message.
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
