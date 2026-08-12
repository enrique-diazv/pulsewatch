import { apiRequest } from '../../services/api/client.ts'
import type { DashboardSummary } from './types.ts'

export function getDashboardSummary() {
    return apiRequest<DashboardSummary>(
        '/dashboard/summary',
        {
            authenticated: true,
        },
    )
}