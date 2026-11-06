import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import i18n, { type Language } from '@/i18n'
import { SidebarBody } from '../Sidebar'

const LABELS: Record<Language, string[]> = {
  th: ['แดชบอร์ด', 'บันทึกเหตุการณ์', 'ผู้ช่วย AI', 'รายงาน', 'โซนพื้นที่', 'ตั้งค่า'],
  en: ['Dashboard', 'Events', 'AI assistant', 'Reports', 'Zones', 'Settings'],
}

async function renderNav(lang: Language) {
  await i18n.changeLanguage(lang)
  // SidebarBody reads app status via a context that has a usable default, so only a router is needed.
  render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <SidebarBody />
    </MemoryRouter>,
  )
}

afterEach(cleanup)

describe('sidebar navigation', () => {
  it.each(['th', 'en'] as const)('renders the six nav labels in %s', async (lang) => {
    await renderNav(lang)
    const links = screen.getAllByRole('link')
    expect(links.map((a) => a.textContent)).toEqual(LABELS[lang])
    expect(document.documentElement.lang).toBe(lang)
  })

  it('links point at the expected routes', async () => {
    await renderNav('en')
    const hrefs = screen.getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(hrefs).toEqual(['/dashboard', '/events', '/assistant', '/reports', '/zones', '/settings'])
  })
})
