import { FileText, Loader2, Scale, Trash2 } from 'lucide-react'
import { useState } from 'react'
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
import { formatBytes, formatNumber, formatThaiDate } from '@/lib/format'
import { SectionCard } from './SectionCard'
import { toastUploadResult } from './UploadResultToast'

const TYPE_BADGE = { md: 'info', txt: 'secondary', pdf: 'danger' } as const

export function RegulationsCard() {
  const docs = useAsync((s) => api.regulations(s), [])
  const [uploading, setUploading] = useState(false)
  const [deleting, setDeleting] = useState<string | null>(null)

  const upload = async (files: File[]) => {
    setUploading(true)
    try {
      toastUploadResult(await api.uploadRegulations(files))
      docs.reload()
    } catch (err) {
      toast.error('อัปโหลดไม่สำเร็จ', { description: toErrorMessage(err) })
    } finally {
      setUploading(false)
    }
  }

  const remove = async (name: string) => {
    if (!window.confirm(`ลบเอกสาร "${name}" ใช่หรือไม่?`)) return
    setDeleting(name)
    try {
      await api.deleteRegulation(name)
      docs.setData((prev) => prev?.filter((d) => d.name !== name))
      toast.success('ลบเอกสารแล้ว', { description: name })
    } catch (err) {
      toast.error('ลบไม่สำเร็จ', { description: toErrorMessage(err) })
    } finally {
      setDeleting(null)
    }
  }

  return (
    <SectionCard
      icon={Scale}
      title="เอกสารกฎระเบียบ"
      description="เอกสารเหล่านี้จะถูกส่งเป็นบริบทให้ผู้ช่วย AI และรายงาน"
      action={docs.data && <Badge variant="secondary">{docs.data.length} ไฟล์</Badge>}
    >
      <FileDropzone
        accept=".md,.txt,.pdf"
        onFiles={(f) => void upload(f)}
        disabled={uploading}
        title={uploading ? 'กำลังอัปโหลด…' : 'ลากไฟล์เอกสารมาวางที่นี่'}
        hint="รองรับ .md .txt .pdf"
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
          <EmptyState icon={FileText} title="ยังไม่มีเอกสาร" description="เพิ่มกฎกระทรวงหรือคู่มือความปลอดภัยของบริษัท" className="py-6" />
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
                    {formatBytes(d.size)} · {formatNumber(d.chars)} ตัวอักษร · แก้ไข {formatThaiDate(d.modified)}
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
                  aria-label={`ลบ ${d.name}`}
                  className="text-slate-400 hover:bg-rose-50 hover:text-rose-600"
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
