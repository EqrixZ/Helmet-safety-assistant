// Chart palette: orange = violations (primary), slate = totals. Categorical order validated for CVD separation.
export const CHART = {
  violation: '#F28C28',
  violationSoft: '#FDE3C8',
  total: '#94A3B8',
  totalSoft: '#E2E8F0',
  grid: '#EEF2F6',
  axis: '#94A3B8',
} as const

export const CATEGORICAL = ['#F28C28', '#3B82F6', '#14B8A6', '#8B5CF6', '#64748B'] as const

export function categoricalColor(index: number): string {
  return CATEGORICAL[index % CATEGORICAL.length] ?? '#64748B'
}

export const AXIS_TICK = { fill: CHART.axis, fontSize: 11 } as const
