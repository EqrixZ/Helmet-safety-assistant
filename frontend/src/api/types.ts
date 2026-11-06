// Mirrors CONTRACT.md §4 exactly. Do not diverge without updating CONTRACT_CHANGES.md.

export type DataSource = 'real' | 'sample'

/** UI / generated-content language sent to the backend. */
export type Language = 'th' | 'en'

export type Event = {
  event_id: string
  datetime: string
  date: string
  time: string
  camera: string
  zone: string
  clip: string
  hardhat: number
  no_hardhat: number
  total_person: number
  violation: boolean
  max_conf: number
  frame_path: string // basename or ""
  frame_url: string | null // "/api/frames/{frame_path}" or null when frame_path empty
  no_hardhat_max: number // raw max Head count before temporal voting
  no_hardhat_ratio: number | null // share of sampled frames with a Head box; null for legacy logs
}

export type Paginated<T> = { items: T[]; total: number; page: number; size: number; pages: number }

export type AggregateRow = { key: string; events: number; violations: number; rate: number } // rate 0..1

export type Trend = { current: number; previous: number; change_pct: number | null } // null when previous == 0

export type Stats = {
  from: string | null
  to: string | null
  total_events: number
  total_violations: number
  violation_rate: number
  total_persons: number
  total_no_hardhat: number
  top_zone: { key: string; violations: number } | null
  top_hour: { key: string; violations: number } | null
  trend: { events: Trend; violations: Trend; violation_rate: Trend }
  data_source: DataSource
}

export type Health = {
  status: 'ok'
  data_source: DataSource
  events_count: number
  date_range: { min: string | null; max: string | null }
  llm_configured: boolean
  llm_model: string
  llm_base_url: string
  llm_provider: LlmProvider | null // provider that answered last (or will be tried first)
  llm_fallback_configured: boolean
  llm_rpm: number
  conf_threshold: number
  model_repo: string
  site_name: string
  version: string
}

export type ChatRole = 'user' | 'assistant'
export type ChatMessage = { role: ChatRole; content: string }
export type ChatRequest = { messages: ChatMessage[]; language?: Language }
export type SuggestionsRequest = { language?: Language }

export type Suggestions = { questions: string[] }

export type ReportType = 'daily' | 'weekly'
export type ReportRequest = { type: ReportType; date: string; language?: Language }
// name: report_{type}_{date}_{lang}.md (legacy reports have no language suffix and language 'th')
export type Report = {
  name: string
  type: ReportType
  date: string
  created_at: string
  markdown: string
  language: Language
}
export type ReportMeta = {
  name: string
  type: ReportType
  date: string
  created_at: string
  size: number
  language: Language
}

export type DetectState = 'idle' | 'running' | 'done' | 'error'
export type DetectStatus = {
  state: DetectState
  progress: number
  processed: number
  total: number
  current_clip: string | null
  message: string
  started_at: string | null
  finished_at: string | null
  events_written: number
}

export type ClipInfo = {
  name: string
  size: number
  parsed: { camera: string; zone: string; datetime: string; matched: boolean }
}
export type UploadResult = { saved: string[]; rejected: { name: string; reason: string }[] }

export type RegulationDoc = { name: string; size: number; type: 'md' | 'txt' | 'pdf'; chars: number; modified: string }

export type Settings = { site_name: string }
export type DetectionKind = 'hardhat' | 'no_hardhat'
export type ModelInfo = {
  path: string
  source: 'local' | 'downloaded'
  family: string | null
  class_names: string[]
  class_mapping: Record<string, DetectionKind>
  fallback_repo: string
  fallback_file: string
  thresholds: Record<DetectionKind, number>
  violation_frame_ratio: number
}

export type LlmProvider = { name: 'primary' | 'fallback'; model: string; base_url: string }

export type LlmTestResult = { ok: boolean; model: string; base_url: string; latency_ms: number | null; message: string }
export type ContextSources = {
  regulation_files: string[]
  log_range: { min: string | null; max: string | null }
  events_count: number
  data_source: DataSource
  log_included_full: boolean
  regulation_paragraphs: string[] // "file · rule title" of each paragraph sent to the LLM
  regulation_paragraphs_total: number
  log_rows: number // event lines sent to the LLM
  log_filter: string // how those rows were chosen (in the requested language)
  token_estimate: number // prompt length / 3.5
}

export type ZoneSummary = AggregateRow & { sparkline: number[] }

export type ErrorCode =
  | 'NOT_FOUND'
  | 'BAD_REQUEST'
  | 'VALIDATION_ERROR'
  | 'LLM_NOT_CONFIGURED'
  | 'LLM_ERROR'
  | 'DETECTION_RUNNING'
  | 'INTERNAL_ERROR'

export type ErrorEnvelope = { error: { code: ErrorCode | string; message: string } }

// §5 SSE events for POST /api/chat
export type ChatStreamEvent =
  | { type: 'sources'; sources: ContextSources }
  | { type: 'token'; content: string }
  | { type: 'error'; message: string }
  | { type: 'done' }

export type GroupBy = 'zone' | 'camera' | 'hour' | 'day'
export type SortOrder = 'asc' | 'desc'

export type DateRange = { from?: string; to?: string }

export type EventQuery = DateRange & {
  zone?: string
  camera?: string
  violation?: boolean
  page?: number
  size?: number
  sort?: string
  order?: SortOrder
}
