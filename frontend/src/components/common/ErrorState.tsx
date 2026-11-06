import { RefreshCw, ServerCrash } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { describeError } from '@/api/client'
import { Button } from '@/components/ui/button'
import { EmptyState } from './EmptyState'

export function ErrorState({ error, onRetry, className }: { error: unknown; onRetry?: () => void; className?: string }) {
  const { t } = useTranslation()
  const info = describeError(error)
  return (
    <EmptyState
      tone="danger"
      icon={ServerCrash}
      title={t('common.loadFailed')}
      description={
        <>
          {info.title}
          {info.detail && <span className="mt-1 block text-xs text-slate-400">{info.detail}</span>}
        </>
      }
      className={className}
      action={
        onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            <RefreshCw /> {t('common.retry')}
          </Button>
        )
      }
    />
  )
}
