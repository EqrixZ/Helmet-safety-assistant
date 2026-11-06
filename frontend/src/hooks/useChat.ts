import { useCallback, useEffect, useRef, useState } from 'react'
import { streamChat } from '@/api/chat'
import { ApiError, toErrorMessage } from '@/api/client'
import i18n, { currentLang } from '@/i18n'
import type { ChatMessage, ContextSources } from '@/api/types'

const STORAGE_KEY = 'hsa.chat.v1'

export type UiMessage = ChatMessage & {
  id: string
  /** assistant only: stream in progress */
  streaming?: boolean
  /** assistant only: stream failed / was stopped */
  error?: string
  stopped?: boolean
}

/** `error` is kept raw so it is translated at render time (see describeError). */
export type ChatFailure = { kind: 'llm_not_configured' | 'error'; error: unknown }

function uid(): string {
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36)
}

function isUiMessage(v: unknown): v is UiMessage {
  if (typeof v !== 'object' || v === null) return false
  const m = v as Record<string, unknown>
  return typeof m.id === 'string' && typeof m.content === 'string' && (m.role === 'user' || m.role === 'assistant')
}

function load(): UiMessage[] {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter(isUiMessage).map((m) => ({ ...m, streaming: false }))
  } catch {
    return []
  }
}

export function useChat() {
  const [messages, setMessages] = useState<UiMessage[]>(load)
  const [sources, setSources] = useState<ContextSources | null>(null)
  const [failure, setFailure] = useState<ChatFailure | null>(null)
  const [busy, setBusy] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.filter((m) => !m.streaming || m.content)))
    } catch {
      /* storage unavailable — ignore */
    }
  }, [messages])

  useEffect(() => () => abortRef.current?.abort(), [])

  const patchAssistant = useCallback((id: string, patch: (m: UiMessage) => Partial<UiMessage>) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch(m) } : m)))
  }, [])

  const send = useCallback(
    async (text: string) => {
      const content = text.trim()
      if (!content || busy) return
      setFailure(null)
      const userMsg: UiMessage = { id: uid(), role: 'user', content }
      const assistantId = uid()
      // History for the API: completed turns only (skip failed/empty assistant replies).
      const history: ChatMessage[] = [...messages, userMsg]
        .filter((m) => m.content.trim() !== '' && !(m.role === 'assistant' && m.error && !m.content))
        .map(({ role, content: c }) => ({ role, content: c }))

      setMessages((prev) => [...prev, userMsg, { id: assistantId, role: 'assistant', content: '', streaming: true }])
      setBusy(true)
      const ctrl = new AbortController()
      abortRef.current = ctrl

      try {
        await streamChat(
          { messages: history, language: currentLang() },
          (evt) => {
            switch (evt.type) {
              case 'sources':
                setSources(evt.sources)
                break
              case 'token':
                patchAssistant(assistantId, (m) => ({ content: m.content + evt.content }))
                break
              case 'error':
                patchAssistant(assistantId, () => ({ error: `${i18n.t('assistant.message.streamError')} — ${evt.message}` }))
                break
              case 'done':
                patchAssistant(assistantId, () => ({ streaming: false }))
                break
            }
          },
          ctrl.signal,
        )
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          patchAssistant(assistantId, () => ({ streaming: false, stopped: true }))
        } else if (err instanceof ApiError && err.isLlmNotConfigured) {
          setMessages((prev) => prev.filter((m) => m.id !== assistantId))
          setFailure({ kind: 'llm_not_configured', error: err })
        } else {
          patchAssistant(assistantId, () => ({ streaming: false, error: toErrorMessage(err) }))
        }
      } finally {
        patchAssistant(assistantId, () => ({ streaming: false }))
        abortRef.current = null
        setBusy(false)
      }
    },
    [busy, messages, patchAssistant],
  )

  const stop = useCallback(() => abortRef.current?.abort(), [])

  const clear = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setFailure(null)
  }, [])

  return { messages, sources, failure, busy, send, stop, clear, dismissFailure: () => setFailure(null) }
}
