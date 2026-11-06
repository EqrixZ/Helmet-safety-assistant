---
version: alpha
name: Helmet Safety Assistant
description: The design language of the Helmet Safety Assistant web console — a Thai-language safety-operations dashboard for construction sites. A dark slate sidebar frames a light slate-50 content area of white, softly shadowed rounded cards; a single chromatic accent, safety orange #F28C28, marks primary actions, the active navigation item and every "violation" data point, while semantic rose / emerald / amber carry status. Type is Inter paired with Noto Sans Thai, with Noto Serif Thai reserved for printed-report headings.

colors:
  # Brand
  primary: "#f28c28"            # safety orange — primary buttons, active nav bar, focus ring, violation series
  primary-hover: "#e07b17"
  on-primary: "#ffffff"
  primary-soft: "#fef3e9"       # primary at 10% on white — icon chips, default badge
  primary-text: "#b45f0c"       # orange text on primary-soft (default badge)
  # Surfaces
  canvas: "#f8fafc"             # slate-50 — page background
  card: "#ffffff"
  surface-muted: "#f1f5f9"      # slate-100 — secondary buttons, muted blocks, code
  table-header: "#f8fafc"       # slate-50 at 80%
  sidebar-top: "#0f172a"        # slate-900 — sidebar gradient start
  sidebar-bottom: "#020617"     # slate-950 — sidebar gradient end
  topbar: "#ffffff"             # at 80% opacity with backdrop blur
  # Text
  ink: "#0f172a"                # slate-900 — headings, values
  body: "#334155"               # slate-700
  mute: "#64748b"               # slate-500 — descriptions, labels
  subtle: "#94a3b8"             # slate-400 — captions, axis ticks, inactive nav text
  sidebar-text-active: "#ffffff"
  # Lines
  hairline: "#e2e8f0"           # slate-200 — borders, inputs, dividers
  chart-grid: "#eef2f6"
  # Semantic
  danger: "#e11d48"             # rose-600 — destructive button; violation badge uses rose-50 / rose-200 / rose-700
  danger-soft: "#fff1f2"
  danger-text: "#be123c"
  success: "#10b981"            # emerald-500 — "online" status dot; safe badge uses emerald-50 / emerald-200 / emerald-700
  success-soft: "#ecfdf5"
  success-text: "#047857"
  warning: "#f59e0b"            # amber-500 — "degraded"/fallback status dot; sample-data badge uses amber-50 / amber-700
  warning-soft: "#fffbeb"
  warning-text: "#b45309"
  info-soft: "#f0f9ff"
  info-text: "#0369a1"
  # Data visualisation
  chart-violation: "#f28c28"
  chart-violation-soft: "#fde3c8"
  chart-total: "#94a3b8"
  chart-total-soft: "#e2e8f0"
  chart-cat-1: "#f28c28"
  chart-cat-2: "#3b82f6"
  chart-cat-3: "#14b8a6"
  chart-cat-4: "#8b5cf6"
  chart-cat-5: "#64748b"

typography:
  page-title:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 24px
    fontWeight: 700
    lineHeight: 32px
    letterSpacing: -0.025em
  kpi-value:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 28px
    fontWeight: 700
    lineHeight: 35px
    letterSpacing: -0.025em
  card-title:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 15px
    fontWeight: 600
    lineHeight: 19px
  body-sm:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
  label:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 13px
    fontWeight: 500
    lineHeight: 18px
  caption:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 12px
    fontWeight: 400
    lineHeight: 16px
  badge:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 12px
    fontWeight: 500
    lineHeight: 16px
  micro:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 11px
    fontWeight: 400
    lineHeight: 16px
  nav-section:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 11px
    fontWeight: 600
    lineHeight: 16px
    letterSpacing: 0.05em
    textTransform: uppercase
  button-md:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 14px
    fontWeight: 500
    lineHeight: 20px
  button-sm:
    fontFamily: Inter, Noto Sans Thai, ui-sans-serif, system-ui, sans-serif
    fontSize: 12px
    fontWeight: 500
    lineHeight: 16px
  report-h1:
    fontFamily: Noto Serif Thai, Inter, Noto Sans Thai, Georgia, serif
    fontSize: 26px
    fontWeight: 700
    lineHeight: 34px
  report-h2:
    fontFamily: Noto Serif Thai, Inter, Noto Sans Thai, Georgia, serif
    fontSize: 18px
    fontWeight: 600
    lineHeight: 28px
  mono:
    fontFamily: ui-monospace, SFMono-Regular, Menlo, monospace
    fontSize: 12px
    fontWeight: 400
    lineHeight: 16px

rounded:
  none: 0px
  sm: 8px          # skeleton-in-tray, report tray   (--radius - 4px)
  md: 10px         # small buttons, skeletons, bubble tail corner (--radius - 2px)
  lg: 12px         # buttons, inputs, nav items, icon chips, tooltips (--radius = 0.75rem)
  xl: 16px         # cards, suggestion tiles (--radius + 4px)
  2xl: 16px        # chat bubbles
  full: 9999px     # badges, status pills, avatars, chips

spacing:          # Tailwind 4px scale; values below are the ones the UI actually uses
  xxs: 2px
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px         # card padding
  2xl: 24px        # page section gap, page gutter (sm+)
  3xl: 32px        # page gutter (lg+)
  4xl: 56px        # report paper padding (sm+)

shadows:
  card: "0 1px 2px rgba(15,23,42,0.04), 0 4px 16px -4px rgba(15,23,42,0.06)"
  card-hover: "Tailwind shadow-md + translateY(-2px)"
  button-primary: "shadow-sm tinted with primary at 30%"
  tooltip: "Tailwind shadow-lg"
  paper: "0 1px 3px rgba(15,23,42,0.08), 0 12px 40px -12px rgba(15,23,42,0.25)"

motion:
  fade-in: "opacity 0→1, 0.35s ease-out"
  slide-up: "opacity 0→1 + translateY(8px→0), 0.4s cubic-bezier(0.16,1,0.3,1) — every card on mount, KPI cards staggered"
  sheet-in: "translateX(100%→0), 0.3s — event drawer from the right, mobile menu from the left"
  indeterminate: "1.4s ease-in-out infinite — report-generation progress bar"
  caret-blink: "1s step-end infinite — orange 2px caret while a chat reply streams"
  status-ping: "Tailwind animate-ping behind status dots"
  press: "buttons scale to 0.98 while active"

layout:
  sidebar-width: 256px          # lg and up
  sidebar-width-compact: 72px   # md–lg: icons only, tooltips for labels
  sidebar-mobile: "sheet from the left, 288px, below md"
  topbar-height: 64px
  content-max-width: 1400px
  page-gutter: "16px / 24px (sm) / 32px (lg)"
  drawer-max-width: 576px
  report-paper-width: 210mm

components:
  app-sidebar:
    background: "linear-gradient({colors.sidebar-top}, {colors.sidebar-bottom})"
    textColor: "{colors.subtle}"
    padding: "20px 12px"
    contents: "logo (orange gradient hard-hat tile + 'Helmet Safety / Assistant · AI Monitoring'), section label, nav, bottom info card (white/3% fill, white/5% border, emerald shield icon, version)"
  nav-item:
    typography: "{typography.body-sm} weight 500"
    textColor: "{colors.subtle}"
    rounded: "{rounded.lg}"
    padding: "10px 12px"
    hover: "white 4% fill, slate-100 text"
    active: "white 8% fill, white text, orange icon, 3px {colors.primary} bar on the left edge"
  top-bar:
    backgroundColor: "{colors.topbar} at 80% + backdrop-blur"
    borderBottom: "{colors.hairline}"
    height: 64px
    contents: "building icon tile, site name (editable in Settings), current page · Thai Buddhist-era date, Backend + LLM status pills"
  status-pill:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.full}"
    typography: "{typography.badge}"
    padding: "6px 12px"
    dot: "10px dot with ping — ok {colors.success}, warn {colors.warning} (LLM missing or on fallback, label 'LLM (สำรอง)'), down #f43f5e, pending #cbd5e1"
  page-header:
    title: "{typography.page-title} {colors.ink}"
    description: "{typography.body-sm} {colors.mute}"
    actions: "right-aligned on sm+ (date-range picker, presets, buttons)"
  card:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.hairline} at 80%"
    rounded: "{rounded.xl}"
    shadow: "{shadows.card}"
    header: "20px sides, 20px top; title {typography.card-title}; description {typography.caption} {colors.mute}"
    content: "20px sides, 16px top, 20px bottom"
    enter: "{motion.slide-up}"
  kpi-card:
    extends: card
    padding: 20px
    label: "{typography.label} {colors.mute}"
    value: "{typography.kpi-value} {colors.ink}"
    iconChip: "36px, {rounded.lg}; tints — orange {colors.primary-soft}/{colors.primary}, rose-50/rose-500, slate-100/slate-600, amber"
    trend: "arrow + % chip ({rounded.md}, 11px semibold): bad = rose-50/rose-600, good = emerald-50/emerald-600, neutral = slate-100/slate-500; for violations 'up' is bad; 'ไม่มีข้อมูลช่วงก่อนหน้า' when there is no previous period"
    hover: "{shadows.card-hover}"
  button-primary:
    backgroundColor: "{colors.primary}"
    hover: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button-md}"
    rounded: "{rounded.lg}"
    height: 36px
    padding: "0 16px"
    shadow: "{shadows.button-primary}"
  button-outline:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.hairline}"
    hover: "slate-50 fill"
  button-secondary:
    backgroundColor: "{colors.surface-muted}"
    hover: "slate-200 fill"
  button-ghost:
    backgroundColor: transparent
    hover: "slate-100 fill"
  button-dark:
    backgroundColor: "{colors.ink}"
    textColor: "#ffffff"
    use: "print / save as PDF"
  button-destructive:
    backgroundColor: "{colors.danger}"
    textColor: "#ffffff"
  button-sizes: "sm 32px ({rounded.md}, {typography.button-sm}, 12px padding) · default 36px · lg 40px (24px padding) · icon 36px / icon-sm 32px"
  focus-ring: "3px ring in {colors.primary} at 40% (buttons) / 20% plus orange border (inputs)"
  text-input:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.lg}"
    height: 36px
    padding: "4px 12px"
    typography: "{typography.body-sm}"
    placeholder: "{colors.mute}"
  segmented-control:
    track: "{colors.surface-muted}, {rounded.lg}, 4px padding"
    segment: "{rounded.md}, 6px 12px, {typography.badge}"
    active: "white segment with shadow-sm and {colors.ink} text — daily / weekly report type, 7 วัน / 14 วัน / ทั้งหมด presets"
  badge:
    rounded: "{rounded.full}"
    typography: "{typography.badge}"
    padding: "2px 8px"
    variants: "default (orange soft), secondary, outline, danger, success, warning, info, dark"
  badge-violation: "danger variant + shield icon — label 'ไม่สวมหมวก'"
  badge-safe: "success variant — label 'ปลอดภัย'"
  badge-data-source: "success 'ข้อมูลจริง' / warning 'ข้อมูลตัวอย่าง'"
  data-table:
    headerBackground: "{colors.table-header}"
    headerTypography: "{typography.caption} weight 500, {colors.mute}"
    body: "{typography.body-sm}, row dividers slate-100 (#f1f5f9), row hover orange-50 at 40% (a faint primary tint), whole row clickable"
    cellPadding: "12px"
    extras: "sortable headers (orange arrow when active), thumbnail column, confidence as % with a small bar, pagination with dark current-page button"
  event-drawer:
    side: right
    maxWidth: 576px
    contents: "annotated frame, 2-column metadata tiles (slate-50, {rounded.lg}), orange full-width 'ถามผู้ช่วยเกี่ยวกับเหตุการณ์นี้' button pinned to the bottom"
  chart-card:
    extends: card
    legend: "small colour dots in the header — violations {colors.chart-violation}, totals {colors.chart-total-soft}"
    axes: "{typography.micro} {colors.subtle}, no axis lines, horizontal grid {colors.chart-grid} only"
    charts: "daily area (orange line + orange→transparent gradient over a slate totals line), zone horizontal bars and hour bars (slate total bar beside orange violation bar, 4px top radius), camera donut with centred total, zone sparklines"
  chart-tooltip:
    backgroundColor: "white at 95% + backdrop blur"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.lg}"
    padding: "8px 12px"
    typography: "{typography.caption}; values semibold, tabular numbers"
  chat-bubble-user:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.2xl} with the top-right corner at {rounded.md}"
    padding: "10px 16px"
    maxWidth: 80%
    avatar: "32px orange-100 circle with user icon, on the right"
  chat-bubble-assistant:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.hairline} at 80%"
    rounded: "{rounded.2xl} with the top-left corner at {rounded.md}"
    padding: "12px 16px"
    content: "markdown (tables, lists) in prose-slate; copy button under the bubble"
    avatar: "32px circle, slate-800→slate-950 gradient, orange bot icon, 2px white ring"
    streaming: "three bouncing slate dots before the first token, then {motion.caret-blink}"
  suggestion-chip:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.full} (row above the input) / {rounded.xl} tiles (empty-state grid)"
    typography: "{typography.badge} {colors.body}"
  chat-input:
    rounded: "{rounded.xl}"
    border: "orange border + ring when focused"
    contents: "auto-growing textarea, round orange send button, hint 'Enter เพื่อส่ง · Shift + Enter ขึ้นบรรทัดใหม่'"
  context-panel:
    placement: "right column of the assistant page (collapsible on tablet)"
    contents: "log section (event count, rows sent, filter used, date range, data-source badge), regulation paragraphs list, estimated context tokens in mono"
  report-paper:
    tray: "slate-200 at 60%, {rounded.sm}, 12–24px padding"
    paper: "white, square corners, max width 210mm, 32–56px padding, {shadows.paper}"
    headings: "{typography.report-h1} / {typography.report-h2} with a hairline under each h2"
    body: "prose-slate markdown, tables and inline frame images"
    print: "a separate print-only copy on A4 with 16mm margins"
  progress-indeterminate:
    track: "{colors.surface-muted}"
    bar: "{colors.primary}, {motion.indeterminate}"
  empty-state:
    layout: "centred, 48px vertical padding"
    icon: "icon tile with a blurred halo (primary at 10%, or rose-100 for errors)"
    text: "title {colors.ink} + description {colors.mute} + optional action button"
  skeleton:
    backgroundColor: "slate-200 at 70%"
    rounded: "{rounded.md}"
    animation: pulse
  toast:
    library: sonner
    position: "top-right"
    use: "upload results, detection finished, settings saved, errors"

---

## Overview

Helmet Safety Assistant is a safety-operations console for a construction site. A safety officer uses it to watch helmet violations detected on CCTV clips, ask an AI assistant about them, and print daily or weekly reports. The interface is entirely in Thai, and the design is built for fast, trustworthy scanning of safety data rather than for marketing.

The shell is a classic operations layout. A **dark slate sidebar** (`{colors.sidebar-top}` → `{colors.sidebar-bottom}` gradient) holds the logo and six sections: แดชบอร์ด, บันทึกเหตุการณ์, ผู้ช่วย AI, รายงาน, โซนพื้นที่ and ตั้งค่า. A **translucent white top bar** shows the site name, the Buddhist-era date and two live status pills (Backend, LLM). Everything else sits on a **light slate-50 canvas** (`{colors.canvas}`) as white cards with a 16px radius and a very soft two-layer shadow. The sidebar collapses to a 72px icon rail on tablets and to a slide-in sheet on phones.

Colour is disciplined. **Safety orange `#F28C28` is the only brand hue.** It marks primary buttons, the active navigation bar, focus rings, the user's chat bubbles, and every "violation" series in the charts. Totals are always drawn in neutral slate beside it, so the orange always means "something went wrong here". Status uses a separate semantic set: rose for violations ("ไม่สวมหมวก"), emerald for safe or online ("ปลอดภัย", status OK), and amber for degraded states (sample data, LLM on the fallback provider).

Type pairs **Inter with Noto Sans Thai**, so Latin identifiers (EVT-0058, cam4) and Thai text share one rhythm. Hierarchy comes from size and weight rather than colour: 24px bold page titles, 28px bold KPI values, 15px semibold card titles, 14px body, and 11–13px labels. **Noto Serif Thai** appears in only one place, the headings of the printable report, which gives the A4 "paper" the feel of an official document.

Motion is small and purposeful. Cards slide up 8px as they mount (KPI cards staggered), status dots pulse, the chat shows typing dots and then a blinking orange caret while tokens stream, and report generation uses an indeterminate orange progress bar. Every data view has a skeleton for loading and an illustrated empty state.

**Key characteristics:**
- One brand hue, safety orange `{colors.primary}`, reserved for actions and violations; slate neutrals everywhere else.
- A dark slate sidebar against a light slate-50 workspace. The dark/light contrast is structural (navigation versus content), not a dark theme.
- Generous, friendly geometry: 12px buttons, inputs and nav items, 16px cards and chat bubbles, full pills for badges and status.
- Inter + Noto Sans Thai for the UI; Noto Serif Thai only for report headings.
- Soft elevation: two-layer card shadows, a hover lift on KPI cards, a deeper shadow on the report paper.
- Charts are quiet: no axis lines, a light horizontal grid only, orange for violations against slate for totals, and a categorical palette (orange, blue, teal, violet, slate) for cameras.
- Thai-first copy with Buddhist-era dates (e.g. 29 ก.ย. 2569); zone keys are shown as Thai names (เครน, นั่งร้าน, ชั้น 3, คลังวัสดุ, ทางเข้า).

## Known Gaps

- **Dark mode:** not implemented. A `dark` custom variant is declared in the CSS but no dark tokens exist; the sidebar is dark by design, not a theme.
- **Unused token:** `--sidebar: #0b1120` is defined in `index.css`, but the sidebar actually renders a slate-900 → slate-950 gradient. The gradient values are the ones documented above.
- **Semantic colours come from Tailwind's palette** (rose / emerald / amber / sky), not from project CSS variables. Only `destructive` has a variable.
- **Mobile:** layouts are designed down to tablet width. Phone widths work (sheet navigation, stacked cards) but have not been polished.
- **Hover and pressed states** are documented only where they are set explicitly in the components (buttons, nav items, chips, table rows).
