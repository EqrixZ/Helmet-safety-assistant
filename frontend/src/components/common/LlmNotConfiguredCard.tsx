import { KeyRound, Settings } from 'lucide-react'
import { Trans, useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const CODE = <code className="rounded bg-card/70 px-1.5 py-0.5 font-mono text-xs" />

/** `detail` is the server's own message (shown small, under the translated explanation). */
export function LlmNotConfiguredCard({ detail, className }: { detail?: string | null; className?: string }) {
  const { t } = useTranslation()
  return (
    <div className={cn('animate-slide-up rounded-xl bg-orange-soft p-6', className)}>
      <div className="flex gap-4">
        <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-tile-orange text-white">
          <KeyRound className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="font-semibold text-navy">{t('llmCard.title')}</h4>
          <p className="mt-1 text-sm leading-relaxed text-slate-600">{t('llmCard.body')}</p>
          {detail && <p className="mt-1 text-xs leading-relaxed text-slate-500">{detail}</p>}
          <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-slate-600">
            <li>
              <Trans i18nKey="llmCard.step1" components={{ code: CODE }} />
            </li>
            <li>
              <Trans i18nKey="llmCard.step2" components={{ code: CODE }} />
            </li>
            <li>{t('llmCard.step3')}</li>
          </ol>
          <Button asChild variant="outline" size="sm" className="mt-4">
            <Link to="/settings">
              <Settings /> {t('llmCard.goSettings')}
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
