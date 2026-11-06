import i18n from '@/i18n'
import type { ErrorEnvelope } from './types'

/** Error codes from the contract envelope (plus client-side NETWORK_ERROR) → `errors.*` translation keys. */
const CODE_KEYS: Record<string, string> = {
  NOT_FOUND: 'errors.notFound',
  BAD_REQUEST: 'errors.badRequest',
  VALIDATION_ERROR: 'errors.validation',
  LLM_NOT_CONFIGURED: 'errors.llmNotConfigured',
  LLM_ERROR: 'errors.llm',
  DETECTION_RUNNING: 'errors.detectionRunning',
  INTERNAL_ERROR: 'errors.internal',
  NETWORK_ERROR: 'errors.network',
}

/** Fallback keys for non-envelope HTTP errors, by status. */
const STATUS_KEYS: Record<number, string> = {
  400: 'errors.badRequest',
  404: 'errors.notFound',
  409: 'errors.conflict',
  422: 'errors.validation',
  500: 'errors.internal',
  502: 'errors.llm',
  503: 'errors.unavailable',
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }

  get isLlmNotConfigured(): boolean {
    return this.code === 'LLM_NOT_CONFIGURED'
  }

  get isNetwork(): boolean {
    return this.code === 'NETWORK_ERROR'
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (!isRecord(value) || !isRecord(value.error)) return false
  return typeof value.error.code === 'string' && typeof value.error.message === 'string'
}

/** Converts a non-2xx Response into an ApiError, parsing the contract error envelope when present. */
export async function toApiError(res: Response): Promise<ApiError> {
  let body: unknown = null
  try {
    body = await res.json()
  } catch {
    body = null
  }
  if (isErrorEnvelope(body)) return new ApiError(res.status, body.error.code, body.error.message)
  return new ApiError(res.status, 'HTTP_ERROR', `HTTP ${res.status}`)
}

/** A display-ready error: a translated `title` plus the server's own message (if any) as `detail`. */
export type ErrorInfo = { title: string; detail: string | null }

/**
 * Translates an error at display time. Known envelope codes map to `errors.*` keys; the server message
 * (Thai) is kept as detail so nothing is lost. Call during render so a language switch re-translates.
 */
export function describeError(err: unknown): ErrorInfo {
  if (err instanceof ApiError) {
    if (err.code === 'HTTP_ERROR') {
      const key = STATUS_KEYS[err.status]
      return { title: key ? i18n.t(key) : i18n.t('errors.http', { status: err.status }), detail: null }
    }
    if (err.code === 'NETWORK_ERROR') return { title: i18n.t('errors.network'), detail: null }
    const key = CODE_KEYS[err.code]
    const title = key ? i18n.t(key) : i18n.t('errors.http', { status: err.status })
    const detail = err.message && err.message !== title ? err.message : null
    return { title, detail }
  }
  if (err instanceof Error && err.message) return { title: err.message, detail: null }
  return { title: i18n.t('errors.unknown'), detail: null }
}

/** One-line form of describeError, for toast descriptions. */
export function toErrorMessage(err: unknown): string {
  const { title, detail } = describeError(err)
  return detail ? `${title} — ${detail}` : title
}

export type QueryValue = string | number | boolean | null | undefined
export type QueryParams = Record<string, QueryValue>

export function buildQuery(params: QueryParams | undefined): string {
  if (!params) return ''
  const qs = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    qs.set(key, String(value))
  }
  const s = qs.toString()
  return s ? `?${s}` : ''
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  query?: QueryParams
  json?: unknown
  body?: BodyInit
  signal?: AbortSignal
}

/** Low-level fetch that throws ApiError on non-2xx or network failure. */
export async function rawRequest(path: string, opts: RequestOptions = {}): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  let body: BodyInit | undefined = opts.body
  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.json)
  }
  let res: Response
  try {
    res = await fetch(`/api${path}${buildQuery(opts.query)}`, {
      method: opts.method ?? 'GET',
      headers,
      body,
      signal: opts.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError(0, 'NETWORK_ERROR', 'Network error')
  }
  if (!res.ok) throw await toApiError(res)
  return res
}

/** Typed JSON request. The generic is the caller's declaration of the contract response type. */
export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const res = await rawRequest(path, opts)
  const data: T = await res.json()
  return data
}
