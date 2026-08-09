import { useQuery } from '@tanstack/react-query'

import {
  getIncident,
  listIncidents,
} from './api.ts'
import type { IncidentStatus } from './types.ts'

export const incidentKeys = {
  all: ['incidents'] as const,
  list: (status?: IncidentStatus) => [
    'incidents',
    'list',
    status ?? 'ALL',
  ] as const,
  detail: (incidentId: string) => [
    'incidents',
    incidentId,
  ] as const,
}

export function useIncidents(
  status?: IncidentStatus,
) {
  return useQuery({
    queryKey: incidentKeys.list(status),
    queryFn: () => listIncidents(status),
  })
}

export function useIncident(incidentId: string) {
  return useQuery({
    queryKey: incidentKeys.detail(incidentId),
    queryFn: () => getIncident(incidentId),
    enabled: incidentId.length > 0,
  })
}