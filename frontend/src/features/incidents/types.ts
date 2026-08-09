export type IncidentStatus = 'OPEN' | 'RESOLVED'

export interface Incident {
  id: string
  monitor_id: string
  started_at: string
  resolved_at: string | null
  status: IncidentStatus
  failure_reason: string
  initial_check_id: number
  recovery_check_id: number | null
}