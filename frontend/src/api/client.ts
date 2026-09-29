import type { ErrorEnvelope } from './types'

const FALLBACK_MESSAGES: Record<number, string> = {
  400: 'คำขอไม่ถูกต้อง',
  404: 'ไม่พบข้อมูลที่ร้องขอ',
  409: 'มีงานอื่นกำลังทำงานอยู่ กรุณารอสักครู่',
  422: 'ข้อมูลที่ส่งไม่ถูกต้อง',
  500: 'เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์',
  502: 'ไม่สามารถเชื่อมต่อบริการ LLM ได้',
  503: 'บริการยังไม่พร้อมใช้งาน',
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
  const fallback = FALLBACK_MESSAGES[res.status] ?? `เกิดข้อผิดพลาด (HTTP ${res.status})`
  return new ApiError(res.status, 'HTTP_ERROR', fallback)
}

export function toErrorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return 'เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ'
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
    throw new ApiError(0, 'NETWORK_ERROR', 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ กรุณาตรวจสอบว่า backend ทำงานอยู่')
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
