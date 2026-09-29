import { RefreshCw, ServerCrash } from 'lucide-react'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { EmptyState } from './EmptyState'

export function ErrorState({ error, onRetry, className }: { error: unknown; onRetry?: () => void; className?: string }) {
  return (
    <EmptyState
      tone="danger"
      icon={ServerCrash}
      title="โหลดข้อมูลไม่สำเร็จ"
      description={toErrorMessage(error)}
      className={className}
      action={
        onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            <RefreshCw /> ลองอีกครั้ง
          </Button>
        )
      }
    />
  )
}
