import { PageContainer, PageHeader } from '@/components/common/PageHeader'
import { ClipsCard } from '@/components/settings/ClipsCard'
import { DetectionCard } from '@/components/settings/DetectionCard'
import { DetectorCard } from '@/components/settings/DetectorCard'
import { LlmCard } from '@/components/settings/LlmCard'
import { RegulationsCard } from '@/components/settings/RegulationsCard'
import { SiteNameCard } from '@/components/settings/SiteNameCard'

export function SettingsPage() {
  return (
    <PageContainer>
      <PageHeader title="ตั้งค่า" description="จัดการข้อมูลโครงการ คลิปวิดีโอ การตรวจจับ เอกสารกฎระเบียบ และการเชื่อมต่อ AI" />
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
