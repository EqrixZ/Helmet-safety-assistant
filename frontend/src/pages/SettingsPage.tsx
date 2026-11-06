import { useTranslation } from 'react-i18next'
import { PageContainer, PageHeader } from '@/components/common/PageHeader'
import { ClipsCard } from '@/components/settings/ClipsCard'
import { DetectionCard } from '@/components/settings/DetectionCard'
import { DetectorCard } from '@/components/settings/DetectorCard'
import { LlmCard } from '@/components/settings/LlmCard'
import { RegulationsCard } from '@/components/settings/RegulationsCard'
import { SiteNameCard } from '@/components/settings/SiteNameCard'

export function SettingsPage() {
  const { t } = useTranslation()
  return (
    <PageContainer>
      <PageHeader title={t('settings.title')} description={t('settings.description')} />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <SiteNameCard />
        <DetectionCard />
        <ClipsCard />
        <RegulationsCard />
        <LlmCard />
        <DetectorCard />
      </div>
    </PageContainer>
  )
}
