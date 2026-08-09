import type { MonitorStatus } from '../../features/monitors/types.ts'

const statusLabels: Record<MonitorStatus, string> = {
  UP: 'Operational',
  DOWN: 'Down',
  DEGRADED: 'Degraded',
  PAUSED: 'Paused',
  UNKNOWN: 'Unknown',
}

interface MonitorStatusBadgeProps {
  status: MonitorStatus
}

export function MonitorStatusBadge({
  status,
}: MonitorStatusBadgeProps) {
  return (
    <span
      className={`status-badge status-badge--${status.toLowerCase()}`}
    >
      <span aria-hidden="true" className="status-badge__indicator" />
      {statusLabels[status]}
    </span>
  )
}