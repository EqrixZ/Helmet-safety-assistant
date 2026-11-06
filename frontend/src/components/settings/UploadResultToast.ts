import { toast } from 'sonner'
import type { UploadResult } from '@/api/types'
import i18n from '@/i18n'

/** Translated toast headings; server rejection reasons are shown as the detail line. */
export function toastUploadResult(result: UploadResult): void {
  if (result.saved.length) {
    toast.success(i18n.t('settings.upload.saved', { count: result.saved.length }), {
      description: result.saved.join(', '),
    })
  }
  for (const r of result.rejected) {
    toast.error(i18n.t('settings.upload.rejected', { name: r.name }), { description: r.reason })
  }
}
