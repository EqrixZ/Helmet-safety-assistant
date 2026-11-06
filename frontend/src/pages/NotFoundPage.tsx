import { Construction, Home } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  const { t } = useTranslation()
  return (
    <div className="grid min-h-[calc(100dvh-4rem)] place-items-center px-6">
      <div className="animate-slide-up text-center">
        <div className="mx-auto mb-6 grid size-20 place-items-center rounded-3xl bg-tile-blue text-white shadow-card">
          <Construction className="size-10" />
        </div>
        <div className="text-6xl font-extrabold tracking-tight text-slate-900">404</div>
        <h1 className="mt-2 text-lg font-semibold text-slate-800">{t('notFound.title')}</h1>
        <p className="mt-1 text-sm text-slate-500">{t('notFound.description')}</p>
        <Button asChild className="mt-6">
          <Link to="/dashboard">
            <Home /> {t('notFound.back')}
          </Link>
        </Button>
      </div>
    </div>
  )
}
