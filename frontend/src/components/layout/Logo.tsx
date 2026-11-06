export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center justify-center">
      {compact ? (
        <span className="text-[17px] font-bold tracking-tight text-navy" title="Helmet Safety">
          HS
        </span>
      ) : (
        <span className="truncate text-[19px] font-bold tracking-tight text-navy">Helmet Safety</span>
      )}
    </div>
  )
}
