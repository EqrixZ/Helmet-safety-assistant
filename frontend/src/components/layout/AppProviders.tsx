import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '@/api/endpoints'
import type { Health } from '@/api/types'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ThemeProvider } from '@/hooks/useTheme'
import { Toaster } from '@/components/ui/sonner'
import { AppStatusContext, DEFAULT_SITE_NAME } from '@/hooks/useAppStatus'
import { DataVersionContext } from '@/hooks/useDataVersion'

const HEALTH_INTERVAL_MS = 30_000

export function AppProviders({ children }: { children: ReactNode }) {
  const [version, setVersion] = useState(0)
  const [health, setHealth] = useState<Health | undefined>(undefined)
  const [healthChecked, setHealthChecked] = useState(false)
  const [backendOnline, setBackendOnline] = useState(false)
  const [siteName, setSiteName] = useState(DEFAULT_SITE_NAME)
  const [healthTick, setHealthTick] = useState(0)

  const invalidate = useCallback(() => {
    setVersion((v) => v + 1)
    setHealthTick((t) => t + 1)
  }, [])
  const refreshHealth = useCallback(() => setHealthTick((t) => t + 1), [])

  useEffect(() => {
    let cancelled = false
    const ctrl = new AbortController()
    const check = () => {
      api
        .health(ctrl.signal)
        .then((h) => {
          if (cancelled) return
          setHealth(h)
          setBackendOnline(true)
        })
        .catch(() => {
          if (!cancelled) setBackendOnline(false)
        })
        .finally(() => {
          if (!cancelled) setHealthChecked(true)
        })
    }
    check()
    const id = window.setInterval(check, HEALTH_INTERVAL_MS)
    return () => {
      cancelled = true
      ctrl.abort()
      window.clearInterval(id)
    }
  }, [healthTick])

  useEffect(() => {
    const ctrl = new AbortController()
    api
      .settings(ctrl.signal)
      .then((s) => setSiteName(s.site_name || DEFAULT_SITE_NAME))
      .catch(() => {})
    return () => ctrl.abort()
  }, [version])

  const status = useMemo(
    () => ({
      health,
      healthChecked,
      backendOnline,
      siteName,
      setSiteName,
      refreshHealth,
    }),
    [health, healthChecked, backendOnline, siteName, refreshHealth],
  )
  const dataVersion = useMemo(() => ({ version, invalidate }), [version, invalidate])

  return (
    <ThemeProvider>
      <DataVersionContext.Provider value={dataVersion}>
        <AppStatusContext.Provider value={status}>
          <TooltipProvider delayDuration={200}>
            {children}
            <Toaster />
          </TooltipProvider>
        </AppStatusContext.Provider>
      </DataVersionContext.Provider>
    </ThemeProvider>
  )
}
