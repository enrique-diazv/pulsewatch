const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ??
  'http://localhost:8000/api/v1'
).replace(/\/$/, '')

let accessToken: string | null = null

export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(
    message: string,
    status: number,
    payload: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

interface ApiRequestOptions
  extends Omit<RequestInit, 'body'> {
  authenticated?: boolean
  json?: unknown
}

export function setAccessToken(token: string) {
  accessToken = token
}

export function clearAccessToken() {
  accessToken = null
}

export function buildWebSocketUrl(path: string): URL {
  const url = new URL(
    `${apiBaseUrl}${path}`,
    window.location.origin,
  )

  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'

  return url
}

function extractErrorMessage(payload: unknown) {
  if (
    typeof payload === 'object' &&
    payload !== null &&
    'detail' in payload &&
    typeof payload.detail === 'string'
  ) {
    return payload.detail
  }

  return 'The request could not be completed'
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const {
    authenticated = false,
    headers: customHeaders,
    json,
    ...requestOptions
  } = options
  const headers = new Headers(customHeaders)

  if (json !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  if (authenticated && accessToken !== null) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...requestOptions,
    body: json === undefined ? undefined : JSON.stringify(json),
    credentials: 'include',
    headers,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('content-type')
  const payload = contentType?.includes('application/json')
    ? await response.json()
    : null

  if (!response.ok) {
    throw new ApiError(
      extractErrorMessage(payload),
      response.status,
      payload,
    )
  }

  return payload as T
}