import { type DependencyList, useCallback, useEffect, useRef, useState } from 'react'
import { useDataVersion } from './useDataVersion'

export type AsyncState<T> = {
  data: T | undefined
  error: unknown
  loading: boolean
  reload: () => void
  setData: (updater: (prev: T | undefined) => T | undefined) => void
}

/**
 * Minimal data-fetching hook: runs `fn` whenever `deps` (or the global data version) change,
 * aborts the previous request, and keeps the last data while reloading.
 */
export function useAsync<T>(
  fn: (signal: AbortSignal) => Promise<T>,
  deps: DependencyList,
  options: { enabled?: boolean } = {},
): AsyncState<T> {
  const enabled = options.enabled ?? true
  const { version } = useDataVersion()
  const [data, setDataState] = useState<T | undefined>(undefined)
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState<boolean>(enabled)
  const [tick, setTick] = useState(0)
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    if (!enabled) {
      setLoading(false)
      return
    }
    const ctrl = new AbortController()
    setLoading(true)
    setError(null)
    fnRef
      .current(ctrl.signal)
      .then((result) => {
        if (!ctrl.signal.aborted) setDataState(result)
      })
      .catch((err: unknown) => {
        if (ctrl.signal.aborted) return
        setError(err)
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false)
      })
    return () => ctrl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, version, tick, enabled])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  const setData = useCallback((updater: (prev: T | undefined) => T | undefined) => setDataState(updater), [])

  return { data, error, loading, reload, setData }
}
