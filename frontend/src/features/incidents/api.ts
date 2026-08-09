import { apiRequest } from '../../services/api/client.ts'
import type {
  Incident,
  IncidentStatus,
} from './types.ts'

export function listIncidents(
  status?: IncidentStatus,
) {
  const search = new URLSearchParams()

  if (status !== undefined) {
    search.set('status', status)
  }

  const query = search.toString()
  const path = query
    ? `/incidents?${query}`
    : '/incidents'

  return apiRequest<Incident[]>(path, {
    authenticated: true,
  })
}

export function getIncident(incidentId: string) {
  return apiRequest<Incident>(
    `/incidents/${incidentId}`,
    {
      authenticated: true,
    },
  )
}