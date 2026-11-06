import { Building2, Check, Loader2 } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAppStatus } from '@/hooks/useAppStatus'
import { SectionCard } from './SectionCard'

export function SiteNameCard() {
  const { t } = useTranslation()
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
      toast.success(t('settings.site.saved'))
    } catch (err) {
      toast.error(t('settings.site.saveFailed'), { description: toErrorMessage(err) })
    } finally {
      setSaving(false)
    }
  }

  return (
    <SectionCard icon={Building2} title={t('settings.site.title')} description={t('settings.site.description')}>
      <form onSubmit={(e) => void save(e)} className="space-y-1.5">
        <Label htmlFor="site-name">{t('settings.site.label')}</Label>
        <div className="flex gap-2">
          <Input
            id="site-name"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={t('common.defaultSiteName')}
            maxLength={120}
          />
          <Button type="submit" disabled={!dirty || saving}>
            {saving ? <Loader2 className="animate-spin" /> : <Check />} {t('settings.site.save')}
          </Button>
        </div>
      </form>
    </SectionCard>
  )
}
