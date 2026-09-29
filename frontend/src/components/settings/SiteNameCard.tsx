import { Building2, Check, Loader2 } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAppStatus } from '@/hooks/useAppStatus'
import { SectionCard } from './SectionCard'

export function SiteNameCard() {
  const { siteName, setSiteName } = useAppStatus()
  const [value, setValue] = useState(siteName)
  const [saving, setSaving] = useState(false)
  useEffect(() => setValue(siteName), [siteName])

  const dirty = value.trim() !== siteName && value.trim() !== ''

  const save = async (e: FormEvent) => {
    e.preventDefault()
    if (!dirty) return
    setSaving(true)
    try {
      const s = await api.updateSettings({ site_name: value.trim() })
      setSiteName(s.site_name)
      toast.success('บันทึกชื่อโครงการแล้ว')
    } catch (err) {
      toast.error('บันทึกไม่สำเร็จ', { description: toErrorMessage(err) })
    } finally {
      setSaving(false)
    }
  }

  return (
    <SectionCard icon={Building2} title="ข้อมูลโครงการ" description="ชื่อนี้จะแสดงที่แถบด้านบนและในรายงาน">
      <form onSubmit={(e) => void save(e)} className="space-y-1.5">
        <Label htmlFor="site-name">ชื่อโครงการ / ไซต์งาน</Label>
        <div className="flex gap-2">
          <Input id="site-name" value={value} onChange={(e) => setValue(e.target.value)} maxLength={120} />
          <Button type="submit" disabled={!dirty || saving}>
            {saving ? <Loader2 className="animate-spin" /> : <Check />} บันทึก
          </Button>
        </div>
      </form>
    </SectionCard>
  )
}
