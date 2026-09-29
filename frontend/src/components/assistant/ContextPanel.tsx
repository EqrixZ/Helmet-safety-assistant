import { CalendarRange, Coins, Database, FileText, Info, ScrollText } from 'lucide-react'
import type { ContextSources } from '@/api/types'
import { DataSourceBadge } from '@/components/common/StatusBadges'
import { Skeleton } from '@/components/ui/skeleton'
import { formatNumber, formatThaiDate } from '@/lib/format'

export function ContextPanel({ sources, loading }: { sources: ContextSources | undefined; loading: boolean }) {
  return (
    <div className="flex h-full flex-col gap-5 p-5">
      <div>
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Database className="size-4 text-primary" /> แหล่งข้อมูลในบริบท
        </h3>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">ข้อมูลที่ผู้ช่วยใช้อ้างอิงในการตอบคำถามแต่ละครั้ง</p>
      </div>

      {loading && !sources ? (
        <div className="space-y-3">
          <Skeleton className="h-16" />
          <Skeleton className="h-24" />
        </div>
      ) : sources ? (
        <>
          <section className="space-y-2.5 rounded-xl border border-slate-200 bg-white p-3.5">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
                <ScrollText className="size-3.5" /> บันทึกเหตุการณ์
              </span>
              <DataSourceBadge source={sources.data_source} />
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-slate-50 p-2">
                <div className="text-slate-500">จำนวนเหตุการณ์</div>
                <div className="mt-0.5 text-base font-bold text-slate-900 tabular-nums">{formatNumber(sources.events_count)}</div>
              </div>
              <div className="rounded-lg bg-slate-50 p-2">
                <div className="text-slate-500">ส่งเข้าบริบท</div>
                <div className="mt-0.5 text-sm font-semibold text-slate-800">
                  สถิติ + {formatNumber(sources.log_rows)} แถว
                </div>
              </div>
            </div>
            {sources.log_filter && <p className="text-[11px] leading-relaxed text-slate-500">{sources.log_filter}</p>}
            <div className="flex items-center gap-1.5 text-xs text-slate-600">
              <CalendarRange className="size-3.5 text-slate-400" />
              {formatThaiDate(sources.log_range.min)} – {formatThaiDate(sources.log_range.max)}
            </div>
          </section>

          <section className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span className="flex items-center gap-1.5">
                <FileText className="size-3.5" /> เอกสารกฎระเบียบ
              </span>
              <span className="text-slate-400">
                {sources.regulation_paragraphs.length}/{sources.regulation_paragraphs_total} ย่อหน้า
              </span>
            </div>
            {sources.regulation_paragraphs.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-200 p-3 text-xs text-slate-500">
                ยังไม่มีเอกสาร — อัปโหลดได้ที่หน้าตั้งค่า
              </div>
            ) : (
              <ul className="space-y-1.5">
                {sources.regulation_paragraphs.map((p, i) => (
                  <li key={`${i}-${p}`} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs text-slate-700">
                    <FileText className="size-3.5 shrink-0 text-primary/70" />
                    <span className="truncate" title={p}>
                      {p}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs">
            <span className="flex items-center gap-1.5 font-semibold text-slate-700">
              <Coins className="size-3.5" /> ขนาดบริบทโดยประมาณ
            </span>
            <span className="font-mono tabular-nums text-slate-800" title="ประมาณจากความยาวข้อความ ÷ 3.5">
              ~{formatNumber(sources.token_estimate)} tokens
            </span>
          </div>
        </>
      ) : (
        <div className="text-xs text-slate-500">ไม่สามารถโหลดข้อมูลบริบทได้</div>
      )}

      <div className="mt-auto flex gap-2 rounded-lg bg-slate-100/80 p-3 text-[11px] leading-relaxed text-slate-500">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        ผู้ช่วยตอบจากข้อมูลในระบบเท่านั้น ควรตรวจสอบกับเจ้าหน้าที่ความปลอดภัยก่อนดำเนินการ
      </div>
    </div>
  )
}
