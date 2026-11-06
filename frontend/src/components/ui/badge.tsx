import { type VariantProps, cva } from 'class-variance-authority'
import type { ComponentProps } from 'react'
import { cn } from '@/lib/utils'

export const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap [&_svg]:size-3 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-blue-soft text-blue-ink',
        secondary: 'border-transparent bg-slate-100 text-slate-700',
        outline: 'border-slate-200 text-slate-700 bg-card',
        danger: 'border-transparent bg-red-soft text-red-ink',
        success: 'border-transparent bg-green-soft text-green-ink',
        warning: 'border-transparent bg-orange-soft text-orange-ink',
        info: 'border-transparent bg-blue-soft text-blue-ink',
        dark: 'border-slate-700 bg-slate-800 text-slate-200',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export function Badge({ className, variant, ...props }: ComponentProps<'span'> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}
