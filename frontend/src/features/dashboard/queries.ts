import { useQuery } from '@tanstack/react-query'

import { getDashboardSummary } from './api.ts'

export const dashboardKeys = {
    summary: ['dashboard', 'summary'] as const,
}

export function useDashboardSummary() {
    return useQuery({
        queryKey: dashboardKeys.summary,
        queryFn: getDashboardSummary,
        refetchInterval: 30_000,
    })
}