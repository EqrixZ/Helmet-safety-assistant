import { useMemo } from 'react'
import { useTheme } from '@/hooks/useTheme'

/** Resolved chart colours for the active theme (Recharts writes SVG attributes, which can't use var()). */
export type ChartTheme = {
  violation: string
  violationSoft: string
  total: string
  totalSoft: string
  grid: string
  axis: string
  label: string
  surface: string
  categorical: readonly string[]
  axisTick: { fill: string; fontSize: number }
  gridProps: { vertical: false; stroke: string; strokeDasharray: string }
}

function readTokens(): ChartTheme {
  const css = getComputedStyle(document.documentElement)
  const v = (name: string) => css.getPropertyValue(name).trim()
  const axis = v('--text-secondary')
  const grid = v('--chart-grid')
  return {
    violation: v('--primary'),
    violationSoft: v('--blue-soft'),
    total: v('--chart-total'),
    totalSoft: v('--slate-200'),
    grid,
    axis,
    label: v('--text-primary'),
    surface: v('--surface'),
    categorical: [v('--tile-blue'), v('--tile-green'), v('--tile-orange'), v('--tile-red'), v('--chart-violet')],
    axisTick: { fill: axis, fontSize: 11 },
    gridProps: { vertical: false, stroke: grid, strokeDasharray: '4 4' },
  }
}

/** Chart colours from the theme tokens; recomputed whenever the theme changes. */
export function useChartTheme(): ChartTheme {
  const { theme } = useTheme()
  // `theme` is the trigger: data-theme has already changed when it does, so the tokens re-resolve.
  return useMemo(() => readTokens(), [theme])
}

export function categoricalColor(palette: ChartTheme, index: number): string {
  return palette.categorical[index % palette.categorical.length] ?? palette.axis
}
