import { Construction, Home } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="grid min-h-[calc(100dvh-4rem)] place-items-center px-6">
      <div className="animate-slide-up text-center">
        <div className="mx-auto mb-6 grid size-20 place-items-center rounded-3xl bg-gradient-to-br from-[#F7A34B] to-[#E0761A] text-white shadow-xl shadow-primary/30">
          <Construction className="size-10" />
        </div>
        <div className="text-6xl font-extrabold tracking-tight text-slate-900">404</div>
        <h1 className="mt-2 text-lg font-semibold text-slate-800">ไม่พบหน้าที่คุณต้องการ</h1>
        <p className="mt-1 text-sm text-slate-500">พื้นที่นี้อาจกำลังก่อสร้าง หรือลิงก์ไม่ถูกต้อง</p>
        <Button asChild className="mt-6">
          <Link to="/dashboard">
            <Home /> กลับหน้าแดชบอร์ด
          </Link>
        </Button>
      </div>
    </div>
  )
}
