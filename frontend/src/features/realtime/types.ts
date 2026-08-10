import type { MonitorStatus } from '../monitors/types.ts'

export type RealtimeEventType =
    | 'monitor.updated'
    | 'incident.opened'
    | 'incident.resolved'

export interface RealtimeTicketResponse {
    ticket: string
    expires_in: number
}

export interface RealtimeEvent {
    event_id: string
    type: RealtimeEventType
    occurred_at: string
    monitor_id: string
    monitor_status: MonitorStatus
    check_id: number
    incident_id: string | null
}