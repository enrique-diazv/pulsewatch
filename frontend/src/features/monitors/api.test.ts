import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import { apiRequest } from '../../services/api/client.ts'
import {
    createMonitor,
    deleteMonitor,
    getMonitor,
    getMonitorMetrics,
    listMonitorChecks,
    listMonitors,
    pauseMonitor,
    queueMonitorCheck,
    resumeMonitor,
    updateMonitor,
} from './api.ts'
import type {
    MonitorCreateInput,
    MonitorUpdateInput,
} from './types.ts'

vi.mock('../../services/api/client.ts')

const mockedApiRequest = vi.mocked(apiRequest)
const monitorId = 'monitor-123'

beforeEach(() => {
    vi.resetAllMocks()
    mockedApiRequest.mockResolvedValue(undefined)
})

describe('monitor API reads and actions', () => {
    it.each([
        {
            name: 'lists monitors',
            execute: () => listMonitors(),
            path: '/monitors',
            options: {
                authenticated: true,
            },
        },
        {
            name: 'gets one monitor',
            execute: () => getMonitor(monitorId),
            path: `/monitors/${monitorId}`,
            options: {
                authenticated: true,
            },
        },
        {
            name: 'deletes a monitor',
            execute: () => deleteMonitor(monitorId),
            path: `/monitors/${monitorId}`,
            options: {
                authenticated: true,
                method: 'DELETE',
            },
        },
        {
            name: 'pauses a monitor',
            execute: () => pauseMonitor(monitorId),
            path: `/monitors/${monitorId}/pause`,
            options: {
                authenticated: true,
                method: 'POST',
            },
        },
        {
            name: 'resumes a monitor',
            execute: () => resumeMonitor(monitorId),
            path: `/monitors/${monitorId}/resume`,
            options: {
                authenticated: true,
                method: 'POST',
            },
        },
        {
            name: 'queues a manual check',
            execute: () => queueMonitorCheck(monitorId),
            path: `/monitors/${monitorId}/check`,
            options: {
                authenticated: true,
                method: 'POST',
            },
        },
        {
            name: 'lists checks with the default limit',
            execute: () => listMonitorChecks(monitorId),
            path: `/monitors/${monitorId}/checks?limit=100`,
            options: {
                authenticated: true,
            },
        },
        {
            name: 'gets metrics for a selected range',
            execute: () =>
                getMonitorMetrics(monitorId, '7d'),
            path: `/monitors/${monitorId}/metrics?range=7d`,
            options: {
                authenticated: true,
            },
        },
    ])('$name', async ({
        execute,
        path,
        options,
    }) => {
        await execute()

        expect(mockedApiRequest).toHaveBeenCalledWith(
            path,
            options,
        )
    })
})

describe('monitor API mutations', () => {
    it('creates a monitor', async () => {
        const input: MonitorCreateInput = {
            name: 'Production API',
            url: 'https://api.example.com/health',
            method: 'GET',
            interval_seconds: 60,
            timeout_seconds: 5,
            expected_status: 200,
            failure_threshold: 3,
            recovery_threshold: 2,
        }

        await createMonitor(input)

        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/monitors',
            {
                authenticated: true,
                method: 'POST',
                json: input,
            },
        )
    })

    it('updates a monitor', async () => {
        const input: MonitorUpdateInput = {
            name: 'Updated API',
            interval_seconds: 120,
        }

        await updateMonitor(monitorId, input)

        expect(mockedApiRequest).toHaveBeenCalledWith(
            `/monitors/${monitorId}`,
            {
                authenticated: true,
                method: 'PATCH',
                json: input,
            },
        )
    })
})