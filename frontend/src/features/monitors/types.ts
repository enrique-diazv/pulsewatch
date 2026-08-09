export type MonitorStatus =
  | 'UP'
  | 'DOWN'
  | 'DEGRADED'
  | 'PAUSED'
  | 'UNKNOWN'

export type HttpMethod = 'GET'

export interface Monitor {
  id: string
  name: string
  url: string
  method: HttpMethod
  interval_seconds: number
  timeout_seconds: number
  expected_status: number
  status: MonitorStatus
  failure_threshold: number
  recovery_threshold: number
  is_active: boolean
  last_checked_at: string | null
  next_check_at: string
  created_at: string
  updated_at: string
}

export interface MonitorCreateInput {
  name: string
  url: string
  method?: HttpMethod
  interval_seconds: number
  timeout_seconds: number
  expected_status: number
  failure_threshold: number
  recovery_threshold: number
}

export type MonitorUpdateInput =
  Partial<MonitorCreateInput>

export interface CheckQueuedResponse {
  task_id: string
  status: 'queued'
}

export interface MonitorCheck {
  id: number
  monitor_id: string
  checked_at: string
  success: boolean
  status_code: number | null
  response_time_ms: number
  error_type: string | null
  error_message: string | null
}