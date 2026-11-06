import { BrainCircuit, CheckCircle2, Loader2, PlugZap, XCircle } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import type { LlmTestResult } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAppStatus } from '@/hooks/useAppStatus'
import { formatNumber } from '@/lib/format'
import { cn } from '@/lib/utils'
import { InfoRow, SectionCard } from './SectionCard'

export function LlmCard() {
  const { health } = useAppStatus()
  const { t } = useTranslation()
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<LlmTestResult | null>(null)

  const test = async () => {
    setTesting(true)
    setResult(null)
    try {
      setResult(await api.testLlm())
    } catch (err) {
      toast.error(t('settings.llm.testFailedToast'), { description: toErrorMessage(err) })
    } finally {
      setTesting(false)
    }
  }

  return (
    <SectionCard
      icon={BrainCircuit}
      title={t('settings.llm.title')}
      description={t('settings.llm.description')}
      action={
        health && (
          <Badge variant={health.llm_configured ? 'success' : 'warning'}>
            {health.llm_configured ? t('settings.llm.configured') : t('settings.llm.notConfigured')}
          </Badge>
        )
      }
    >
      <div>
        <InfoRow label={t('settings.llm.model')} value={health?.llm_model ?? '—'} mono />
        <InfoRow label="Base URL" value={health?.llm_base_url ?? '—'} mono />
        <InfoRow label="API Key" value={health ? (health.llm_configured ? '••••••••' : t('settings.llm.none')) : '—'} />
      </div>
      <Button variant="outline" className="mt-4 w-full" onClick={() => void test()} disabled={testing}>
        {testing ? <Loader2 className="animate-spin" /> : <PlugZap />} {t('settings.llm.test')}
      </Button>
      {result && (
        <div
          className={cn(
            'animate-slide-up mt-3 flex items-start gap-2.5 rounded-lg border p-3 text-sm',
            result.ok ? 'border-transparent bg-green-soft text-green-ink' : 'border-transparent bg-red-soft text-red-ink',
          )}
        >
          {result.ok ? <CheckCircle2 className="mt-0.5 size-4 shrink-0" /> : <XCircle className="mt-0.5 size-4 shrink-0" />}
          <div className="min-w-0">
            {/* Sentence built from structured fields; on failure the server message is the detail. */}
            <div className="font-medium">
              {result.ok ? t('settings.llm.testOk', { model: result.model }) : t('settings.llm.testFailed')}
            </div>
            {!result.ok && result.message && <div className="mt-0.5 text-xs opacity-80">{result.message}</div>}
            <div className="mt-0.5 text-xs opacity-80">
              {result.model}
              {result.latency_ms !== null && ` · ${t('settings.llm.latency', { ms: formatNumber(result.latency_ms) })}`}
            </div>
          </div>
        </div>
      )}
    </SectionCard>
  )
}
