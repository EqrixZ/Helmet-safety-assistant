import { rawRequest } from './client'
import i18n from '@/i18n'
import type { ChatRequest, ChatStreamEvent } from './types'

function isChatStreamEvent(value: unknown): value is ChatStreamEvent {
  if (typeof value !== 'object' || value === null || !('type' in value)) return false
  const t = (value as { type: unknown }).type
  return t === 'sources' || t === 'token' || t === 'error' || t === 'done'
}

/** Parses one SSE event block ("data: ...\n" lines) into a ChatStreamEvent. */
function parseBlock(block: string): ChatStreamEvent | null {
  const dataLines: string[] = []
  for (const rawLine of block.split('\n')) {
    const line = rawLine.replace(/\r$/, '')
    if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''))
  }
  if (dataLines.length === 0) return null
  try {
    const parsed: unknown = JSON.parse(dataLines.join('\n'))
    return isChatStreamEvent(parsed) ? parsed : null
  } catch {
    return null
  }
}

/**
 * POST /api/chat and stream SSE events (CONTRACT §5).
 * Throws ApiError before streaming for non-2xx (e.g. 503 LLM_NOT_CONFIGURED JSON envelope).
 * Resolves when the stream ends; the caller receives a final `done` event.
 */
export async function streamChat(
  body: ChatRequest,
  onEvent: (event: ChatStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await rawRequest('/chat', { method: 'POST', json: body, signal })
  if (!res.body) throw new Error(i18n.t('errors.streamUnsupported'))

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let sawDone = false

  const flush = (final: boolean) => {
    buffer = buffer.replace(/\r\n/g, '\n')
    let idx = buffer.indexOf('\n\n')
    while (idx !== -1) {
      const block = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      const evt = parseBlock(block)
      if (evt) {
        if (evt.type === 'done') sawDone = true
        onEvent(evt)
      }
      idx = buffer.indexOf('\n\n')
    }
    if (final && buffer.trim()) {
      const evt = parseBlock(buffer)
      buffer = ''
      if (evt) {
        if (evt.type === 'done') sawDone = true
        onEvent(evt)
      }
    }
  }

  try {
    for (;;) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      flush(false)
    }
    buffer += decoder.decode()
    flush(true)
  } finally {
    reader.releaseLock()
  }
  if (!sawDone) onEvent({ type: 'done' })
}
