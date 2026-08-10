import { apiRequest } from '../../services/api/client.ts'
import type {
  CheckQueuedResponse,
  Monitor,
  MonitorCheck,
  MonitorCreateInput,
  MonitorUpdateInput,
  MetricsRange,
  MonitorMetrics,
} from './types.ts'

export function listMonitors() {
  return apiRequest<Monitor[]>('/monitors', {
    authenticated: true,
  })
}

export function getMonitor(monitorId: string) {
  return apiRequest<Monitor>(`/monitors/${monitorId}`, {
    authenticated: true,
  })
}

export function createMonitor(
  input: MonitorCreateInput,
) {
  return apiRequest<Monitor>('/monitors', {
    authenticated: true,
    method: 'POST',
    json: input,
  })
}

export function updateMonitor(
  monitorId: string,
  input: MonitorUpdateInput,
) {
  return apiRequest<Monitor>(`/monitors/${monitorId}`, {
    authenticated: true,
    method: 'PATCH',
    json: input,
  })
}

export function deleteMonitor(monitorId: string) {
  return apiRequest<void>(`/monitors/${monitorId}`, {
    authenticated: true,
    method: 'DELETE',
  })
}

export function pauseMonitor(monitorId: string) {
  return apiRequest<Monitor>(
    `/monitors/${monitorId}/pause`,
    {
      authenticated: true,
      method: 'POST',
    },
  )
}

export function resumeMonitor(monitorId: string) {
  return apiRequest<Monitor>(
    `/monitors/${monitorId}/resume`,
    {
      authenticated: true,
      method: 'POST',
    },
  )
}

export function queueMonitorCheck(monitorId: string) {
  return apiRequest<CheckQueuedResponse>(
    `/monitors/${monitorId}/check`,
    {
      authenticated: true,
      method: 'POST',
    },
  )
}

export function listMonitorChecks(
  monitorId: string,
  limit = 100,
) {
  return apiRequest<MonitorCheck[]>(
    `/monitors/${monitorId}/checks?limit=${limit}`,
    {
      authenticated: true,
    },
  )
}

export function getMonitorMetrics(
  monitorId: string,
  metricsRange: MetricsRange,
) {
  return apiRequest<MonitorMetrics>(
    `/monitors/${monitorId}/metrics?range=${metricsRange}`,
    {
      authenticated: true,
    },
  )
}