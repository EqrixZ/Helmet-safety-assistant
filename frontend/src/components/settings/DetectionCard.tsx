import { CheckCircle2, Loader2, Play, ScanSearch, XCircle } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Trans, useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import type { DetectStatus } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useDataVersion } from '@/hooks/useDataVersion'
import i18n from '@/i18n'
import { formatDateTime } from '@/lib/format'
import { SectionCard } from './SectionCard'

/** The status sentence is built on the client from structured fields (the server's `message` is Thai-only). */
function statusSentence(s: DetectStatus): string {
  if (s.state === 'running') return i18n.t('settings.detection.statusRunning', { processed: s.processed, total: s.total })
  if (s.state === 'done') return i18n.t('settings.detection.statusDone', { count: s.events_written, clips: s.total })
  if (s.state === 'error') return i18n.t('settings.detection.statusError')
  return ''
}

export function DetectionCard() {
  const { t } = useTranslation()
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
            toast.success(i18n.t('settings.detection.doneToast'), {
              description: i18n.t('settings.detection.doneToastDesc', { count: s.events_written }),
            })
            invalidate()
          } else if (s.state === 'error') {
            stopPolling()
            toast.error(i18n.t('settings.detection.failedToast'), { description: s.message })
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
      toast.error(t('settings.detection.startFailed'), { description: toErrorMessage(err) })
    } finally {
      setStarting(false)
    }
  }

  const running = status?.state === 'running'
  return (
    <SectionCard
      icon={ScanSearch}
      title={t('settings.detection.title')}
      description={t('settings.detection.description')}
    >
      <div className="space-y-4">
        <Button onClick={() => void run()} disabled={running || starting} className="w-full" size="lg">
          {running || starting ? <Loader2 className="animate-spin" /> : <Play />}
          {running ? t('settings.detection.running') : t('settings.detection.run')}
        </Button>
        {status && status.state !== 'idle' && (
          <div className="animate-fade-in space-y-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4">
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                {status.state === 'done' && <CheckCircle2 className="size-4 text-tile-green" />}
                {status.state === 'error' && <XCircle className="size-4 text-tile-red" />}
                {status.state === 'running' && <Loader2 className="size-4 animate-spin text-primary" />}
                {status.state === 'done'
                  ? t('settings.detection.stateDone')
                  : status.state === 'error'
                    ? t('settings.detection.stateError')
                    : t('settings.detection.stateRunning')}
              </span>
              <span className="text-slate-500 tabular-nums">
                {t('settings.detection.progress', {
                  processed: status.processed,
                  total: status.total,
                  percent: Math.round(status.progress * 100),
                })}
              </span>
            </div>
            <Progress value={status.progress * 100} />
            <p className="text-xs text-slate-600">{statusSentence(status)}</p>
            {status.state === 'error' && status.message && (
              <p className="text-[11px] text-slate-500">{status.message}</p>
            )}
            {status.current_clip && running && (
              <p className="truncate font-mono text-[11px] text-slate-500">▶ {status.current_clip}</p>
            )}
            {status.finished_at && (
              <p className="text-[11px] text-slate-400">{t('settings.detection.finishedAt', { date: formatDateTime(status.finished_at) })}</p>
            )}
          </div>
        )}
        {(!status || status.state === 'idle') && (
          <p className="text-xs leading-relaxed text-slate-500">
            <Trans i18nKey="settings.detection.idleHint" components={{ code: <code className="font-mono" /> }} />
          </p>
        )}
      </div>
    </SectionCard>
  )
}
