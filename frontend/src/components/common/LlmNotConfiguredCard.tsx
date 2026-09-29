import { KeyRound, Settings } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function LlmNotConfiguredCard({ message, className }: { message?: string; className?: string }) {
  return (
    <div className={cn('animate-slide-up rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50/60 p-5', className)}>
      <div className="flex gap-4">
        <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-amber-100 text-amber-700">
          <KeyRound className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="font-semibold text-amber-900">ยังไม่ได้ตั้งค่าโมเดลภาษา (LLM)</h4>
          <p className="mt-1 text-sm leading-relaxed text-amber-800/90">
            {message ?? 'ยังไม่ได้ตั้งค่า LLM_API_KEY — กรุณาใส่ค่าในไฟล์ .env แล้วรีสตาร์ต backend'}
          </p>
          <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-amber-900/80">
            <li>
              คัดลอกไฟล์ <code className="rounded bg-white/70 px-1.5 py-0.5 font-mono text-xs">.env.example</code> เป็น{' '}
              <code className="rounded bg-white/70 px-1.5 py-0.5 font-mono text-xs">.env</code> ที่รากโปรเจกต์
            </li>
            <li>
              ใส่ค่า <code className="rounded bg-white/70 px-1.5 py-0.5 font-mono text-xs">LLM_API_KEY=...</code> (และ
              LLM_BASE_URL / LLM_MODEL หากไม่ใช้ OpenAI)
            </li>
            <li>รีสตาร์ต backend แล้วลองอีกครั้ง</li>
          </ol>
          <Button asChild variant="outline" size="sm" className="mt-4 border-amber-300 bg-white/80">
            <Link to="/settings">
              <Settings /> ไปที่หน้าตั้งค่า
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
