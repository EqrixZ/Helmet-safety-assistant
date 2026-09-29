import { createContext, useContext } from 'react'
import type { Health } from '@/api/types'

export const DEFAULT_SITE_NAME = 'โครงการก่อสร้างอาคาร A'

export type AppStatus = {
  health: Health | undefined
  /** true once the first health check has completed (success or failure) */
  healthChecked: boolean
  backendOnline: boolean
  siteName: string
  setSiteName: (name: string) => void
  refreshHealth: () => void
}

export const AppStatusContext = createContext<AppStatus>({
  health: undefined,
  healthChecked: false,
  backendOnline: false,
  siteName: DEFAULT_SITE_NAME,
  setSiteName: () => {},
  refreshHealth: () => {},
})

export function useAppStatus(): AppStatus {
  return useContext(AppStatusContext)
}
