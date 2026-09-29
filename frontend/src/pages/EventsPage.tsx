import { Download } from 'lucide-react'
import { api } from '@/api/endpoints'
import { ErrorState } from '@/components/common/ErrorState'
import { PageContainer, PageHeader } from '@/components/common/PageHeader'
import { EventDrawer } from '@/components/events/EventDrawer'
import { EventFilters } from '@/components/events/EventFilters'
import { EventsTable } from '@/components/events/EventsTable'
import { Pagination } from '@/components/events/Pagination'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useAsync } from '@/hooks/useAsync'
import { useEventQuery } from '@/hooks/useEventQuery'
import { formatNumber } from '@/lib/format'
import { downloadText } from '@/lib/utils'
import type { Event } from '@/api/types'

function toCsv(rows: Event[]): string {
  const cols: (keyof Event)[] = ['event_id', 'datetime', 'camera', 'zone', 'hardhat', 'no_hardhat', 'total_person', 'violation', 'max_conf', 'clip']
  return [cols.join(','), ...rows.map((r) => cols.map((c) => String(r[c])).join(','))].join('\n')
}

export function EventsPage() {
  const { query, selectedId, update, toggleSort, clear, activeFilterCount } = useEventQuery()
  const list = useAsync((s) => api.events(query, s), [JSON.stringify(query)])
  const data = list.data
  const selected = data?.items.find((e) => e.event_id === selectedId)

  const exportCsv = async () => {
    const all = await api.events({ ...query, page: 1, size: 200 })
    downloadText('events.csv', `﻿${toCsv(all.items)}`, 'text/csv;charset=utf-8')
  }

  return (
    <PageContainer>
      <PageHeader
        title="บันทึกเหตุการณ์"
        description={
          data ? `พบ ${formatNumber(data.total)} เหตุการณ์ตามตัวกรอง — คลิกแถวเพื่อดูรายละเอียดและภาพเฟรม` : 'รายการเหตุการณ์จากการตรวจจับหมวกนิรภัย'
        }
        actions={
          <Button variant="outline" onClick={() => void exportCsv()} disabled={!data || data.total === 0}>
            <Download /> ส่งออก CSV
          </Button>
        }
      />
      <EventFilters query={query} onChange={update} onClear={clear} activeCount={activeFilterCount} />
      <Card className="overflow-hidden">
        {list.error ? (
          <ErrorState error={list.error} onRetry={list.reload} />
        ) : (
          <>
            <EventsTable
              items={data?.items}
              loading={list.loading}
              query={query}
              onSort={toggleSort}
              onSelect={(e) => update({ event: e.event_id }, false)}
              selectedId={selectedId}
              onClear={clear}
            />
            {data && data.total > 0 && (
              <Pagination
                page={data.page}
                pages={data.pages}
                total={data.total}
                size={data.size}
                onPage={(p) => update({ page: String(p) }, false)}
              />
            )}
          </>
        )}
      </Card>
      <EventDrawer eventId={selectedId} initial={selected} onClose={() => update({ event: undefined }, false)} />
    </PageContainer>
  )
}
