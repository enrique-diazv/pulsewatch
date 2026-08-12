export interface DashboardSummary {
    total_monitors: number
    operational_monitors: number
    down_monitors: number
    degraded_monitors: number
    active_incidents: number
    total_checks: number
    successful_checks: number
    overall_uptime_percentage: number | null
    average_response_time_ms: number | null
}