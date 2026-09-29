import { CheckCircle2, Loader2, Play, ScanSearch, XCircle } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import type { DetectStatus } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useDataVersion } from '@/hooks/useDataVersion'
import { formatThaiDateTime } from '@/lib/format'
import { SectionCard } from './SectionCard'

export function DetectionCard() {
  const { invalidate } = useDataVersion()
  const [status, setStatus] = useState<DetectStatus | null>(null)
  const [starting, setStarting] = useState(false)
  const pollRef = useRef<number | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) window.clearInterval(pollRef.current)
    pollRef.current = null
  }, [])

  const poll = useCallback(() => {
    stopPolling()
    pollRef.current = window.setInterval(() => {
      api
        .detectStatus()
        .then((s) => {
          setStatus(s)
          if (s.state === 'done') {
            stopPolling()
            toast.success('ตรวจจับเสร็จสิ้น', { description: `บันทึก ${s.events_written} เหตุการณ์ — อัปเดตข้อมูลทุกหน้าแล้ว` })
            invalidate()
          } else if (s.state === 'error') {
            stopPolling()
            toast.error('การตรวจจับล้มเหลว', { description: s.message })
          }
        })
        .catch(() => {})
    }, 1000)
  }, [invalidate, stopPolling])

  // Pick up a run that is already in progress (e.g. after navigation).
  useEffect(() => {
    api
      .detectStatus()
      .then((s) => {
        setStatus(s)
        if (s.state === 'running') poll()
      })
      .catch(() => {})
    return stopPolling
  }, [poll, stopPolling])

  const run = async () => {
    setStarting(true)
    try {
      setStatus(await api.detectRun())
      poll()
    } catch (err) {
      toast.error('เริ่มการตรวจจับไม่สำเร็จ', { description: toErrorMessage(err) })
    } finally {
      setStarting(false)
    }
  }

  const running = status?.state === 'running'
  return (
    <SectionCard icon={ScanSearch} title="รันการตรวจจับ" description="ประมวลผลคลิปทั้งหมดด้วย YOLO26s และสร้าง events.csv ใหม่">
      <div className="space-y-4">
        <Button onClick={() => void run()} disabled={running || starting} className="w-full" size="lg">
          {running || starting ? <Loader2 className="animate-spin" /> : <Play />}
          {running ? 'กำลังตรวจจับ…' : 'รันการตรวจจับ'}
        </Button>
        {status && status.state !== 'idle' && (
          <div className="animate-fade-in space-y-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4">
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                {status.state === 'done' && <CheckCircle2 className="size-4 text-emerald-500" />}
                {status.state === 'error' && <XCircle className="size-4 text-rose-500" />}
                {status.state === 'running' && <Loader2 className="size-4 animate-spin text-primary" />}
                {status.state === 'done' ? 'เสร็จสิ้น' : status.state === 'error' ? 'ผิดพลาด' : 'กำลังทำงาน'}
              </span>
              <span className="text-slate-500 tabular-nums">
                {status.processed}/{status.total} คลิป · {Math.round(status.progress * 100)}%
              </span>
            </div>
            <Progress value={status.progress * 100} />
            <p className="text-xs text-slate-600">{status.message}</p>
            {status.current_clip && running && (
              <p className="truncate font-mono text-[11px] text-slate-500">▶ {status.current_clip}</p>
            )}
            {status.finished_at && (
              <p className="text-[11px] text-slate-400">เสร็จเมื่อ {formatThaiDateTime(status.finished_at)}</p>
            )}
          </div>
        )}
        {(!status || status.state === 'idle') && (
          <p className="text-xs leading-relaxed text-slate-500">
            ระบบจะสแกนคลิปทั้งหมดในโฟลเดอร์ <code className="font-mono">data/clips</code> ใหม่ทุกครั้ง และเขียนทับ events.csv
          </p>
        )}
      </div>
    </SectionCard>
  )
}
