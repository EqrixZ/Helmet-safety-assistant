import { AlertTriangle, CheckCircle2, Film, Loader2, Video } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { FileDropzone } from '@/components/common/FileDropzone'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useAsync } from '@/hooks/useAsync'
import { cameraLabel, formatBytes, formatDateTime, zoneLabel } from '@/lib/format'
import { SectionCard } from './SectionCard'
import { toastUploadResult } from './UploadResultToast'

export function ClipsCard() {
  const { t } = useTranslation()
  const clips = useAsync((s) => api.clips(s), [])
  const [uploading, setUploading] = useState(false)

  const upload = async (files: File[]) => {
    setUploading(true)
    try {
      toastUploadResult(await api.uploadClips(files))
      clips.reload()
    } catch (err) {
      toast.error(t('settings.upload.failed'), { description: toErrorMessage(err) })
    } finally {
      setUploading(false)
    }
  }

  return (
    <SectionCard
      icon={Video}
      title={t('settings.clips.title')}
      description={t('settings.clips.description')}
      action={clips.data && <Badge variant="secondary">{t('settings.clips.count', { count: clips.data.length })}</Badge>}
    >
      <FileDropzone
        accept=".mp4,.mov,.avi,.mkv,video/*"
        onFiles={(f) => void upload(f)}
        disabled={uploading}
        title={uploading ? t('settings.upload.uploading') : t('settings.clips.drop')}
        hint={
          <span>
            {t('settings.clips.nameFormat')}{' '}
            <code className="rounded bg-card px-1 font-mono text-[11px] text-slate-700 ring-1 ring-slate-200">cam{'{ID}'}_{'{zone}'}_{'{YYYY-MM-DD}'}_{'{HHMM}'}.mp4</code>
            <br />
            {t('settings.clips.example')} <code className="font-mono text-[11px] text-primary">cam2_crane_2026-09-29_1405.mp4</code>
          </span>
        }
      />
      {uploading && (
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
          <Loader2 className="size-3.5 animate-spin" /> {t('settings.clips.uploadingFiles')}
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
          <EmptyState
            icon={Film}
            title={t('settings.clips.emptyTitle')}
            description={t('settings.clips.emptyDescription')}
            className="py-6"
          />
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
                      ? `${cameraLabel(c.parsed.camera)} · ${zoneLabel(c.parsed.zone)} · ${formatDateTime(c.parsed.datetime)}`
                      : t('settings.clips.fileTime', { date: formatDateTime(c.parsed.datetime) })}{' '}
                    · {formatBytes(c.size)}
                  </div>
                </div>
                {c.parsed.matched ? (
                  <CheckCircle2 className="size-4 shrink-0 text-tile-green" aria-label={t('settings.clips.validName')} />
                ) : (
                  <Badge variant="warning" className="shrink-0">
                    <AlertTriangle /> {t('settings.clips.invalidName')}
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
