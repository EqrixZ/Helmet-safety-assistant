import { Bot, PanelRight, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router-dom'
import { describeError } from '@/api/client'
import { api } from '@/api/endpoints'
import { ChatInput } from '@/components/assistant/ChatInput'
import { ContextPanel } from '@/components/assistant/ContextPanel'
import { MessageBubble } from '@/components/assistant/MessageBubble'
import { SuggestionChips } from '@/components/assistant/SuggestionChips'
import { LlmNotConfiguredCard } from '@/components/common/LlmNotConfiguredCard'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { useAppStatus } from '@/hooks/useAppStatus'
import { useAsync } from '@/hooks/useAsync'
import { useChat } from '@/hooks/useChat'
import { useLang } from '@/i18n'

function readPrefill(state: unknown): string | null {
  if (typeof state === 'object' && state !== null && 'prefill' in state) {
    const v = (state as { prefill: unknown }).prefill
    return typeof v === 'string' ? v : null
  }
  return null
}

function FailureNote({ error }: { error: unknown }) {
  const { title, detail } = describeError(error)
  return (
    <div className="rounded-xl bg-red-soft p-4 text-sm text-red-ink">
      {title}
      {detail && <div className="mt-1 text-xs opacity-80">{detail}</div>}
    </div>
  )
}

export function AssistantPage() {
  const { t } = useTranslation()
  const lang = useLang()
  const location = useLocation()
  const navigate = useNavigate()
  const { health } = useAppStatus()
  const chat = useChat()
  const [input, setInput] = useState(() => readPrefill(location.state) ?? '')
  const [panelOpen, setPanelOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Both come from the server in the active language; re-fetch when it changes.
  const suggestions = useAsync((s) => api.chatSuggestions({ language: lang }, s), [lang])
  const context = useAsync((s) => api.chatContext(lang, s), [lang])
  const sources = chat.sources ?? context.data

  // Consume router state so a refresh doesn't re-apply the prefill.
  useEffect(() => {
    if (readPrefill(location.state)) navigate(location.pathname, { replace: true, state: null })
  }, [location.state, location.pathname, navigate])

  const lastContent = chat.messages[chat.messages.length - 1]?.content
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [chat.messages.length, lastContent, chat.failure])

  const submit = (text: string) => {
    if (!text.trim()) return
    setInput('')
    void chat.send(text)
  }

  const questions = suggestions.data?.questions ?? []
  const empty = chat.messages.length === 0
  const llmMissing = health?.llm_configured === false

  const panel = <ContextPanel sources={sources} loading={context.loading} />

  return (
    <div className="flex h-[calc(100dvh-4rem)] min-h-0">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between gap-3 border-b border-slate-200/80 bg-card/60 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center rounded-xl bg-navy text-card">
              <Bot className="size-5" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-slate-900">{t('assistant.title')}</h1>
              <p className="text-xs text-slate-500">{health ? t('assistant.model', { model: health.llm_model }) : t('assistant.subtitle')}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={chat.clear} disabled={empty && !chat.failure} className="text-slate-500">
              <Trash2 /> <span className="hidden sm:inline">{t('assistant.clear')}</span>
            </Button>
            <Button variant="outline" size="sm" className="xl:hidden" onClick={() => setPanelOpen(true)}>
              <PanelRight /> <span className="hidden sm:inline">{t('assistant.sources')}</span>
            </Button>
          </div>
        </div>

        <div ref={scrollRef} className="scrollbar-thin flex-1 overflow-y-auto">
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6">
            {empty && !chat.failure && (
              <div className="animate-fade-in flex flex-col items-center pt-6 text-center sm:pt-12">
                <div className="relative mb-5">
                  <div className="absolute inset-0 scale-150 rounded-full bg-primary/15 blur-2xl" />
                  <div className="relative grid size-16 place-items-center rounded-2xl bg-tile-blue text-white shadow-card">
                    <Bot className="size-8" />
                  </div>
                </div>
                <h2 className="text-xl font-bold text-slate-900">{t('assistant.greeting')}</h2>
                <p className="mt-2 max-w-md text-sm text-slate-500">
                  {t('assistant.intro')}
                </p>
                {llmMissing && <LlmNotConfiguredCard className="mt-6 w-full text-left" />}
                <div className="mt-8 w-full text-left">
                  <SuggestionChips variant="grid" questions={questions} loading={suggestions.loading} onPick={submit} />
                </div>
              </div>
            )}
            {chat.messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {chat.failure &&
              (chat.failure.kind === 'llm_not_configured' ? (
                <LlmNotConfiguredCard detail={describeError(chat.failure.error).detail} />
              ) : (
                <FailureNote error={chat.failure.error} />
              ))}
          </div>
        </div>

        <div className="border-t border-slate-200/60 bg-gradient-to-t from-slate-50 via-slate-50 to-slate-50/80 px-4 pt-3 pb-4 sm:px-6">
          <div className="mx-auto flex max-w-3xl flex-col gap-2.5">
            {!empty && (
              <SuggestionChips questions={questions} loading={suggestions.loading} onPick={submit} disabled={chat.busy} />
            )}
            <ChatInput value={input} onChange={setInput} onSend={() => submit(input)} onStop={chat.stop} busy={chat.busy} />
          </div>
        </div>
      </div>

      <aside className="hidden w-80 shrink-0 border-l border-slate-200/80 bg-slate-50/80 xl:block">{panel}</aside>
      <Sheet open={panelOpen} onOpenChange={setPanelOpen}>
        <SheetContent className="max-w-sm bg-slate-50">
          <SheetTitle className="sr-only">{t('assistant.sourcesTitle')}</SheetTitle>
          {panel}
        </SheetContent>
      </Sheet>
    </div>
  )
}
