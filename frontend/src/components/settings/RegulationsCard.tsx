import { FileText, Loader2, Scale, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { FileDropzone } from '@/components/common/FileDropzone'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAsync } from '@/hooks/useAsync'
import { formatBytes, formatDate, formatNumber } from '@/lib/format'
import { SectionCard } from './SectionCard'
import { toastUploadResult } from './UploadResultToast'

const TYPE_BADGE = { md: 'info', txt: 'secondary', pdf: 'danger' } as const

export function RegulationsCard() {
  const { t } = useTranslation()
  const docs = useAsync((s) => api.regulations(s), [])
  const [uploading, setUploading] = useState(false)
  const [deleting, setDeleting] = useState<string | null>(null)

  const upload = async (files: File[]) => {
    setUploading(true)
    try {
      toastUploadResult(await api.uploadRegulations(files))
      docs.reload()
    } catch (err) {
      toast.error(t('settings.upload.failed'), { description: toErrorMessage(err) })
    } finally {
      setUploading(false)
    }
  }

  const remove = async (name: string) => {
    if (!window.confirm(t('settings.regs.confirmDelete', { name }))) return
    setDeleting(name)
    try {
      await api.deleteRegulation(name)
      docs.setData((prev) => prev?.filter((d) => d.name !== name))
      toast.success(t('settings.regs.deleted'), { description: name })
    } catch (err) {
      toast.error(t('settings.regs.deleteFailed'), { description: toErrorMessage(err) })
    } finally {
      setDeleting(null)
    }
  }

  return (
    <SectionCard
      icon={Scale}
      title={t('settings.regs.title')}
      description={t('settings.regs.description')}
      action={docs.data && <Badge variant="secondary">{t('settings.regs.count', { count: docs.data.length })}</Badge>}
    >
      <FileDropzone
        accept=".md,.txt,.pdf"
        onFiles={(f) => void upload(f)}
        disabled={uploading}
        title={uploading ? t('settings.upload.uploading') : t('settings.regs.drop')}
        hint={t('settings.regs.supported')}
      />
      <div className="mt-4">
        {docs.loading && !docs.data ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : docs.error ? (
          <ErrorState error={docs.error} onRetry={docs.reload} className="py-6" />
        ) : !docs.data || docs.data.length === 0 ? (
          <EmptyState
            icon={FileText}
            title={t('settings.regs.emptyTitle')}
            description={t('settings.regs.emptyDescription')}
            className="py-6"
          />
        ) : (
          <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">
            {docs.data.map((d) => (
              <li key={d.name} className="group flex items-center gap-3 px-3 py-2.5">
                <FileText className="size-4 shrink-0 text-slate-400" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm text-slate-800" title={d.name}>
                    {d.name}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {t('settings.regs.meta', {
                      size: formatBytes(d.size),
                      chars: formatNumber(d.chars),
                      date: formatDate(d.modified),
                    })}
                  </div>
                </div>
                <Badge variant={TYPE_BADGE[d.type]} className="uppercase">
                  {d.type}
                </Badge>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => void remove(d.name)}
                  disabled={deleting === d.name}
                  aria-label={t('settings.regs.deleteLabel', { name: d.name })}
                  className="text-slate-400 hover:bg-red-soft hover:text-red-ink"
                >
                  {deleting === d.name ? <Loader2 className="animate-spin" /> : <Trash2 />}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </SectionCard>
  )
}
