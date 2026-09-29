import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { EventQuery, SortOrder } from '@/api/types'

export const PAGE_SIZE = 15

/** Event list filters, synced with URL search params (so other pages can deep-link, e.g. ?zone=crane). */
export function useEventQuery() {
  const [params, setParams] = useSearchParams()

  const query = useMemo<EventQuery>(() => {
    const v = params.get('violation')
    const order = params.get('order')
    return {
      from: params.get('from') ?? undefined,
      to: params.get('to') ?? undefined,
      zone: params.get('zone') ?? undefined,
      camera: params.get('camera') ?? undefined,
      violation: v === 'true' ? true : v === 'false' ? false : undefined,
      page: Math.max(1, Number(params.get('page') ?? '1') || 1),
      size: PAGE_SIZE,
      sort: params.get('sort') ?? 'datetime',
      order: (order === 'asc' ? 'asc' : 'desc') satisfies SortOrder,
    }
  }, [params])

  const selectedId = params.get('event')

  const update = useCallback(
    (patch: Record<string, string | undefined>, resetPage = true) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          for (const [k, v] of Object.entries(patch)) {
            if (v === undefined || v === '') next.delete(k)
            else next.set(k, v)
          }
          if (resetPage && !('page' in patch)) next.delete('page')
          return next
        },
        { replace: true },
      )
    },
    [setParams],
  )

  const toggleSort = useCallback(
    (column: string) => {
      const same = query.sort === column
      update({ sort: column, order: same && query.order === 'desc' ? 'asc' : 'desc' })
    },
    [query.sort, query.order, update],
  )

  const clear = useCallback(() => setParams(new URLSearchParams(), { replace: true }), [setParams])

  const activeFilterCount = [query.from, query.to, query.zone, query.camera, query.violation].filter((x) => x !== undefined).length

  return { query, selectedId, update, toggleSort, clear, activeFilterCount }
}
