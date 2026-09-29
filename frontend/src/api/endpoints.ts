import { request } from './client'
import type {
  AggregateRow,
  ClipInfo,
  ContextSources,
  DateRange,
  DetectStatus,
  Event,
  EventQuery,
  GroupBy,
  Health,
  LlmTestResult,
  ModelInfo,
  Paginated,
  RegulationDoc,
  Report,
  ReportMeta,
  ReportRequest,
  Settings,
  Stats,
  Suggestions,
  UploadResult,
  ZoneSummary,
} from './types'

function filesForm(files: File[]): FormData {
  const form = new FormData()
  for (const f of files) form.append('files', f, f.name)
  return form
}

export const api = {
  health: (signal?: AbortSignal) => request<Health>('/health', { signal }),

  stats: (q: DateRange & { zone?: string; camera?: string } = {}, signal?: AbortSignal) =>
    request<Stats>('/stats', { query: q, signal }),

  events: (q: EventQuery = {}, signal?: AbortSignal) =>
    request<Paginated<Event>>('/events', { query: q, signal }),

  event: (id: string, signal?: AbortSignal) => request<Event>(`/events/${encodeURIComponent(id)}`, { signal }),

  aggregates: (groupBy: GroupBy, range: DateRange = {}, signal?: AbortSignal) =>
    request<AggregateRow[]>('/aggregates', { query: { group_by: groupBy, ...range }, signal }),

  zones: (signal?: AbortSignal) => request<ZoneSummary[]>('/zones', { signal }),

  cameras: (signal?: AbortSignal) => request<AggregateRow[]>('/cameras', { signal }),

  chatContext: (signal?: AbortSignal) => request<ContextSources>('/chat/context', { signal }),

  chatSuggestions: (signal?: AbortSignal) =>
    request<Suggestions>('/chat/suggestions', { method: 'POST', json: {}, signal }),

  createReport: (body: ReportRequest, signal?: AbortSignal) =>
    request<Report>('/reports', { method: 'POST', json: body, signal }),

  reports: (signal?: AbortSignal) => request<ReportMeta[]>('/reports', { signal }),

  report: (name: string, signal?: AbortSignal) => request<Report>(`/reports/${encodeURIComponent(name)}`, { signal }),

  detectRun: () => request<DetectStatus>('/detect/run', { method: 'POST', json: {} }),

  detectStatus: (signal?: AbortSignal) => request<DetectStatus>('/detect/status', { signal }),

  modelInfo: (signal?: AbortSignal) => request<ModelInfo>('/detect/model-info', { signal }),

  clips: (signal?: AbortSignal) => request<ClipInfo[]>('/clips', { signal }),

  uploadClips: (files: File[]) => request<UploadResult>('/clips/upload', { method: 'POST', body: filesForm(files) }),

  regulations: (signal?: AbortSignal) => request<RegulationDoc[]>('/regulations', { signal }),

  uploadRegulations: (files: File[]) =>
    request<UploadResult>('/regulations/upload', { method: 'POST', body: filesForm(files) }),

  deleteRegulation: (name: string) =>
    request<{ deleted: string }>(`/regulations/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  settings: (signal?: AbortSignal) => request<Settings>('/settings', { signal }),

  updateSettings: (body: Settings) => request<Settings>('/settings', { method: 'PUT', json: body }),

  testLlm: () => request<LlmTestResult>('/llm/test', { method: 'POST', json: {} }),
}
