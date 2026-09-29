import { ImageOff } from 'lucide-react'
import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

export function FrameImage({
  src,
  alt,
  className,
  compact = false,
}: {
  src: string | null
  alt: string
  className?: string
  compact?: boolean
}) {
  const [failed, setFailed] = useState(false)
  const [loaded, setLoaded] = useState(false)
  useEffect(() => {
    setFailed(false)
    setLoaded(false)
  }, [src])

  if (!src || failed) {
    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center gap-1.5 bg-[repeating-linear-gradient(135deg,#f1f5f9_0_10px,#e2e8f0_10px_20px)] text-slate-400',
          className,
        )}
        aria-label={alt}
        role="img"
      >
        <ImageOff className={compact ? 'size-4' : 'size-7'} />
        {!compact && <span className="text-xs font-medium">ไม่มีภาพเฟรม</span>}
      </div>
    )
  }
  return (
    <div className={cn('relative overflow-hidden bg-slate-100', className)}>
      {!loaded && <div className="absolute inset-0 animate-pulse bg-slate-200/70" />}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        onError={() => setFailed(true)}
        className={cn('h-full w-full object-cover transition-opacity duration-300', loaded ? 'opacity-100' : 'opacity-0')}
      />
    </div>
  )
}
