import { ArrowUp, Square } from 'lucide-react'
import { type KeyboardEvent, useEffect, useRef } from 'react'
import { Trans, useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'

export function ChatInput({
  value,
  onChange,
  onSend,
  onStop,
  busy,
  disabled,
}: {
  value: string
  onChange: (v: string) => void
  onSend: () => void
  onStop: () => void
  busy: boolean
  disabled?: boolean
}) {
  const { t } = useTranslation()
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [value])

  useEffect(() => {
    ref.current?.focus()
  }, [])

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      if (!busy && value.trim()) onSend()
    }
  }

  return (
    <div className="rounded-2xl bg-card p-2 shadow-card transition focus-within:ring-4 focus-within:ring-primary/15">
      <div className="flex items-end gap-2">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={t('assistant.input.placeholder')}
          className="scrollbar-thin max-h-[200px] min-h-10 flex-1 resize-none bg-transparent px-2.5 py-2 text-sm outline-none placeholder:text-slate-400"
        />
        {busy ? (
          <Button size="icon" variant="dark" onClick={onStop} aria-label={t('assistant.input.stop')} className="rounded-xl">
            <Square className="size-3.5 fill-current" />
          </Button>
        ) : (
          <Button size="icon" onClick={onSend} disabled={!value.trim() || disabled} aria-label={t('assistant.input.send')} className="rounded-xl">
            <ArrowUp className="size-4" />
          </Button>
        )}
      </div>
      <div className="flex items-center justify-between px-2.5 pt-1 text-[11px] text-slate-400">
        <span>
          <Trans i18nKey="assistant.input.hint" components={{ k: <kbd className="font-sans" /> }} />
        </span>
        <span className="hidden sm:inline">{t('assistant.input.grounding')}</span>
      </div>
    </div>
  )
}
