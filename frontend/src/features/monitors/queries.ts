import {
    useMutation,
    useQuery,
    useQueryClient,
} from '@tanstack/react-query'

import {
    createMonitor,
    getMonitor,
    listMonitors,
    pauseMonitor,
    queueMonitorCheck,
    resumeMonitor,
    listMonitorChecks,
    deleteMonitor,
    updateMonitor,
} from './api.ts'
import type {
    Monitor,
    MonitorUpdateInput,
} from './types.ts'

export const monitorKeys = {
    all: ['monitors'] as const,
    detail: (monitorId: string) => [
        'monitors',
        monitorId,
    ] as const,
    checks: (monitorId: string) => [
        'monitors',
        monitorId,
        'checks',
    ] as const,
}

function updateMonitorCache(
    monitor: Monitor,
    queryClient: ReturnType<typeof useQueryClient>,
) {
    queryClient.setQueryData(
        monitorKeys.detail(monitor.id),
        monitor,
    )
    void queryClient.invalidateQueries({
        queryKey: monitorKeys.all,
    })
}

export function useMonitors() {
    return useQuery({
        queryKey: monitorKeys.all,
        queryFn: listMonitors,
    })
}

export function useMonitor(monitorId: string) {
    return useQuery({
        queryKey: monitorKeys.detail(monitorId),
        queryFn: () => getMonitor(monitorId),
        enabled: monitorId.length > 0,
    })
}

export function useCreateMonitor() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: createMonitor,
        onSuccess: (monitor) => {
            updateMonitorCache(monitor, queryClient)
        },
    })
}

export function usePauseMonitor() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: pauseMonitor,
        onSuccess: (monitor) => {
            updateMonitorCache(monitor, queryClient)
        },
    })
}

export function useResumeMonitor() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: resumeMonitor,
        onSuccess: (monitor) => {
            updateMonitorCache(monitor, queryClient)
        },
    })
}

export function useQueueMonitorCheck() {
    return useMutation({
        mutationFn: queueMonitorCheck,
    })
}

export function useMonitorChecks(
    monitorId: string,
    limit = 100,
) {
    return useQuery({
        queryKey: monitorKeys.checks(monitorId),
        queryFn: () => listMonitorChecks(monitorId, limit),
        enabled: monitorId.length > 0,
        refetchInterval: 15_000,
    })
}

interface UpdateMonitorVariables {
    monitorId: string
    input: MonitorUpdateInput
}

export function useUpdateMonitor() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({
            monitorId,
            input,
        }: UpdateMonitorVariables) =>
            updateMonitor(monitorId, input),
        onSuccess: (monitor) => {
            updateMonitorCache(monitor, queryClient)
        },
    })
}

export function useDeleteMonitor() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: deleteMonitor,
        onSuccess: (_data, monitorId) => {
            queryClient.removeQueries({
                queryKey: monitorKeys.detail(monitorId),
            })
            void queryClient.invalidateQueries({
                queryKey: monitorKeys.all,
            })
        },
    })
}