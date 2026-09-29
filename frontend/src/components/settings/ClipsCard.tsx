import { AlertTriangle, CheckCircle2, Film, Loader2, Video } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { FileDropzone } from '@/components/common/FileDropzone'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useAsync } from '@/hooks/useAsync'
import { cameraLabel, formatBytes, formatThaiDateTime, zoneLabel } from '@/lib/format'
import { SectionCard } from './SectionCard'
import { toastUploadResult } from './UploadResultToast'

export function ClipsCard() {
  const clips = useAsync((s) => api.clips(s), [])
  const [uploading, setUploading] = useState(false)

  const upload = async (files: File[]) => {
    setUploading(true)
    try {
      toastUploadResult(await api.uploadClips(files))
      clips.reload()
    } catch (err) {
      toast.error('อัปโหลดไม่สำเร็จ', { description: toErrorMessage(err) })
    } finally {
      setUploading(false)
    }
  }

  return (
    <SectionCard
      icon={Video}
      title="คลิปวิดีโอจากกล้อง"
      description="อัปโหลดคลิปเพื่อให้ระบบตรวจจับการสวมหมวกนิรภัย"
      action={clips.data && <Badge variant="secondary">{clips.data.length} คลิป</Badge>}
    >
      <FileDropzone
        accept=".mp4,.mov,.avi,.mkv,video/*"
        onFiles={(f) => void upload(f)}
        disabled={uploading}
        title={uploading ? 'กำลังอัปโหลด…' : 'ลากไฟล์วิดีโอมาวางที่นี่'}
        hint={
          <span>
            รูปแบบชื่อไฟล์ <code className="rounded bg-white px-1 font-mono text-[11px] text-slate-700 ring-1 ring-slate-200">cam{'{ID}'}_{'{zone}'}_{'{YYYY-MM-DD}'}_{'{HHMM}'}.mp4</code>
            <br />
            ตัวอย่าง <code className="font-mono text-[11px] text-primary">cam2_crane_2026-09-29_1405.mp4</code>
          </span>
        }
      />
      {uploading && (
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
          <Loader2 className="size-3.5 animate-spin" /> กำลังอัปโหลดไฟล์…
        </div>
      )}
      <div className="mt-4">
        {clips.loading && !clips.data ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : clips.error ? (
          <ErrorState error={clips.error} onRetry={clips.reload} className="py-6" />
        ) : !clips.data || clips.data.length === 0 ? (
          <EmptyState icon={Film} title="ยังไม่มีคลิป" description="อัปโหลดคลิปจากกล้องวงจรปิดเพื่อเริ่มต้น" className="py-6" />
        ) : (
          <ul className="scrollbar-thin max-h-72 divide-y divide-slate-100 overflow-y-auto rounded-lg border border-slate-200">
            {clips.data.map((c) => (
              <li key={c.name} className="flex items-center gap-3 px-3 py-2.5">
                <Film className="size-4 shrink-0 text-slate-400" />
                <div className="min-w-0 flex-1">
                  <div className="truncate font-mono text-xs text-slate-800" title={c.name}>
                    {c.name}
                  </div>
                  <div className="mt-0.5 truncate text-[11px] text-slate-500">
                    {c.parsed.matched
                      ? `${cameraLabel(c.parsed.camera)} · ${zoneLabel(c.parsed.zone)} · ${formatThaiDateTime(c.parsed.datetime)}`
                      : `ใช้เวลาไฟล์: ${formatThaiDateTime(c.parsed.datetime)}`}{' '}
                    · {formatBytes(c.size)}
                  </div>
                </div>
                {c.parsed.matched ? (
                  <CheckCircle2 className="size-4 shrink-0 text-emerald-500" aria-label="ชื่อไฟล์ถูกต้อง" />
                ) : (
                  <Badge variant="warning" className="shrink-0">
                    <AlertTriangle /> ไม่ตรงรูปแบบ
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </SectionCard>
  )
}
