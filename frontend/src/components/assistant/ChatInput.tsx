import { ArrowUp, Square } from 'lucide-react'
import { type KeyboardEvent, useEffect, useRef } from 'react'
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
    <div className="rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_4px_24px_-8px_rgba(15,23,42,0.12)] transition focus-within:border-primary/60 focus-within:ring-4 focus-within:ring-primary/10">
      <div className="flex items-end gap-2">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="ถามเกี่ยวกับความปลอดภัยในไซต์งาน เช่น “โซนไหนเสี่ยงที่สุดสัปดาห์นี้”"
          className="scrollbar-thin max-h-[200px] min-h-10 flex-1 resize-none bg-transparent px-2.5 py-2 text-sm outline-none placeholder:text-slate-400"
        />
        {busy ? (
          <Button size="icon" variant="dark" onClick={onStop} aria-label="หยุด" className="rounded-xl">
            <Square className="size-3.5 fill-current" />
          </Button>
        ) : (
          <Button size="icon" onClick={onSend} disabled={!value.trim() || disabled} aria-label="ส่ง" className="rounded-xl">
            <ArrowUp className="size-4" />
          </Button>
        )}
      </div>
      <div className="flex items-center justify-between px-2.5 pt-1 text-[11px] text-slate-400">
        <span>
          <kbd className="font-sans">Enter</kbd> เพื่อส่ง · <kbd className="font-sans">Shift + Enter</kbd> ขึ้นบรรทัดใหม่
        </span>
        <span className="hidden sm:inline">คำตอบอ้างอิงจากบันทึกเหตุการณ์และเอกสารกฎระเบียบ</span>
      </div>
    </div>
  )
}
