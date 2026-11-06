import { Database, FlaskConical, ShieldAlert, ShieldCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { DataSource } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

export function ViolationBadge({ violation }: { violation: boolean }) {
  const { t } = useTranslation()
  return violation ? (
    <Badge variant="danger" title={t('common.violationTitle')}>
      <ShieldAlert /> {t('common.violation')}
    </Badge>
  ) : (
    <Badge variant="info" title={t('common.okTitle')}>
      <ShieldCheck /> {t('common.ok')}
    </Badge>
  )
}

export function DataSourceBadge({ source }: { source: DataSource | undefined }) {
  const { t } = useTranslation()
  if (!source) return null
  const real = source === 'real'
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span>
          <Badge variant={real ? 'success' : 'warning'} className="cursor-default">
            {real ? <Database /> : <FlaskConical />}
            {real ? t('common.dataReal') : t('common.dataSample')}
          </Badge>
        </span>
      </TooltipTrigger>
      <TooltipContent>
        {real ? t('common.dataRealTip') : t('common.dataSampleTip')}
      </TooltipContent>
    </Tooltip>
  )
}
