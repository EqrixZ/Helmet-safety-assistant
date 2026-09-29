import { BrainCircuit, CheckCircle2, Loader2, PlugZap, XCircle } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import type { LlmTestResult } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAppStatus } from '@/hooks/useAppStatus'
import { cn } from '@/lib/utils'
import { InfoRow, SectionCard } from './SectionCard'

export function LlmCard() {
  const { health } = useAppStatus()
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<LlmTestResult | null>(null)

  const test = async () => {
    setTesting(true)
    setResult(null)
    try {
      setResult(await api.testLlm())
    } catch (err) {
      toast.error('ทดสอบไม่สำเร็จ', { description: toErrorMessage(err) })
    } finally {
      setTesting(false)
    }
  }

  return (
    <SectionCard
      icon={BrainCircuit}
      title="โมเดลภาษา (LLM)"
      description="ตั้งค่าผ่านตัวแปร LLM_API_KEY, LLM_BASE_URL, LLM_MODEL ในไฟล์ .env"
      action={
        health && (
          <Badge variant={health.llm_configured ? 'success' : 'warning'}>
            {health.llm_configured ? 'ตั้งค่าแล้ว' : 'ยังไม่ได้ตั้งค่า'}
          </Badge>
        )
      }
    >
      <div>
        <InfoRow label="โมเดล" value={health?.llm_model ?? '—'} mono />
        <InfoRow label="Base URL" value={health?.llm_base_url ?? '—'} mono />
        <InfoRow label="API Key" value={health ? (health.llm_configured ? '••••••••' : 'ไม่มี') : '—'} />
      </div>
      <Button variant="outline" className="mt-4 w-full" onClick={() => void test()} disabled={testing}>
        {testing ? <Loader2 className="animate-spin" /> : <PlugZap />} ทดสอบการเชื่อมต่อ
      </Button>
      {result && (
        <div
          className={cn(
            'animate-slide-up mt-3 flex items-start gap-2.5 rounded-lg border p-3 text-sm',
            result.ok ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-rose-200 bg-rose-50 text-rose-800',
          )}
        >
          {result.ok ? <CheckCircle2 className="mt-0.5 size-4 shrink-0" /> : <XCircle className="mt-0.5 size-4 shrink-0" />}
          <div className="min-w-0">
            <div className="font-medium">{result.message}</div>
            <div className="mt-0.5 text-xs opacity-80">
              {result.model}
              {result.latency_ms !== null && ` · ตอบกลับใน ${result.latency_ms.toLocaleString('th-TH')} ms`}
            </div>
          </div>
        </div>
      )}
    </SectionCard>
  )
}
