import { toast } from 'sonner'
import type { UploadResult } from '@/api/types'

export function toastUploadResult(result: UploadResult): void {
  if (result.saved.length) {
    toast.success(`อัปโหลดสำเร็จ ${result.saved.length} ไฟล์`, { description: result.saved.join(', ') })
  }
  for (const r of result.rejected) {
    toast.error(`ไม่รับไฟล์ ${r.name}`, { description: r.reason })
  }
}
