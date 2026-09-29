import { UploadCloud } from 'lucide-react'
import { type DragEvent, type ReactNode, useRef, useState } from 'react'
import { cn } from '@/lib/utils'

export function FileDropzone({
  accept,
  onFiles,
  disabled,
  title,
  hint,
}: {
  accept: string
  onFiles: (files: File[]) => void
  disabled?: boolean
  title: string
  hint?: ReactNode
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)
    if (disabled) return
    const files = Array.from(e.dataTransfer.files)
    if (files.length) onFiles(files)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled) inputRef.current?.click()
      }}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={cn(
        'group flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-all outline-none focus-visible:ring-[3px] focus-visible:ring-primary/30',
        dragging ? 'scale-[1.01] border-primary bg-primary/5' : 'border-slate-200 bg-slate-50/60 hover:border-primary/50 hover:bg-primary/[0.03]',
        disabled && 'pointer-events-none opacity-60',
      )}
    >
      <div
        className={cn(
          'mb-3 grid size-12 place-items-center rounded-xl bg-white shadow-sm ring-1 ring-slate-200 transition',
          dragging ? 'text-primary' : 'text-slate-400 group-hover:text-primary',
        )}
      >
        <UploadCloud className="size-6" />
      </div>
      <div className="text-sm font-medium text-slate-700">
        {title} <span className="text-primary">หรือคลิกเพื่อเลือกไฟล์</span>
      </div>
      {hint && <div className="mt-1.5 text-xs text-slate-500">{hint}</div>}
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const files = Array.from(e.target.files ?? [])
          if (files.length) onFiles(files)
          e.target.value = ''
        }}
      />
    </div>
  )
}
