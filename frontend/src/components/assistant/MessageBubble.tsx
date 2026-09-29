import { AlertTriangle, Bot, Copy, Check, User } from 'lucide-react'
import { useState } from 'react'
import { Markdown } from '@/components/common/Markdown'
import type { UiMessage } from '@/hooks/useChat'
import { cn } from '@/lib/utils'

export function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1.5" aria-label="กำลังพิมพ์">
      {[0, 150, 300].map((d) => (
        <span key={d} className="size-2 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: `${d}ms` }} />
      ))}
    </div>
  )
}

export function BotAvatar() {
  return (
    <div className="grid size-8 shrink-0 place-items-center rounded-full bg-gradient-to-br from-slate-800 to-slate-950 text-primary shadow-sm ring-2 ring-white">
      <Bot className="size-4" />
    </div>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard?.writeText(text).then(() => {
          setCopied(true)
          setTimeout(() => setCopied(false), 1500)
        })
      }}
      className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
    >
      {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
      {copied ? 'คัดลอกแล้ว' : 'คัดลอก'}
    </button>
  )
}

export function MessageBubble({ message }: { message: UiMessage }) {
  if (message.role === 'user') {
    return (
      <div className="animate-slide-up flex justify-end gap-3">
        <div className="max-w-[80%] rounded-2xl rounded-tr-md bg-primary px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap text-white shadow-sm shadow-primary/20">
          {message.content}
        </div>
        <div className="grid size-8 shrink-0 place-items-center rounded-full bg-orange-100 text-primary ring-2 ring-white">
          <User className="size-4" />
        </div>
      </div>
    )
  }
  const waiting = message.streaming && !message.content
  return (
    <div className="animate-slide-up flex gap-3">
      <BotAvatar />
      <div className="min-w-0 max-w-[88%]">
        <div
          className={cn(
            'rounded-2xl rounded-tl-md border border-slate-200/80 bg-white px-4 py-3 shadow-sm',
            message.error && !message.content && 'border-rose-200 bg-rose-50',
          )}
        >
          {waiting ? (
            <TypingDots />
          ) : (
            <div className={cn('relative', message.streaming && 'streaming-caret')}>
              {message.content && (
                <Markdown className="prose-sm text-[14px] leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                  {message.content}
                </Markdown>
              )}
            </div>
          )}
          {message.error && (
            <div className="mt-2 flex items-start gap-2 text-xs text-rose-600">
              <AlertTriangle className="mt-0.5 size-3.5 shrink-0" /> {message.error}
            </div>
          )}
        </div>
        {!message.streaming && message.content && (
          <div className="mt-1 flex items-center gap-2 pl-1">
            <CopyButton text={message.content} />
            {message.stopped && <span className="text-[11px] text-slate-400">หยุดการตอบแล้ว</span>}
          </div>
        )}
      </div>
    </div>
  )
}
