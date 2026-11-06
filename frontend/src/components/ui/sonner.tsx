import { useTranslation } from 'react-i18next'
import { Toaster as Sonner, type ToasterProps } from 'sonner'
import { useTheme } from '@/hooks/useTheme'

export function Toaster(props: ToasterProps) {
  const { theme } = useTheme()
  const { t } = useTranslation()
  return (
    <Sonner
      position="top-right"
      theme={theme}
      richColors
      closeButton
      containerAriaLabel={t('common.notifications')}
      toastOptions={{ className: 'font-sans', closeButtonAriaLabel: t('common.close') }}
      {...props}
    />
  )
}
