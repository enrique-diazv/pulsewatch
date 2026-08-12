import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import type { PropsWithChildren } from 'react'

import { useAuth } from '../auth/useAuth.ts'
import { incidentKeys } from '../incidents/queries.ts'
import { monitorKeys } from '../monitors/queries.ts'
import {
    createRealtimeSocket,
    issueRealtimeTicket,
} from './api.ts'
import type {
    RealtimeEvent,
    RealtimeEventType,
} from './types.ts'
import { dashboardKeys } from '../dashboard/queries.ts'

const INITIAL_RECONNECT_DELAY_MS = 1_000
const MAX_RECONNECT_DELAY_MS = 30_000

const realtimeEventTypes = new Set<RealtimeEventType>([
    'monitor.updated',
    'incident.opened',
    'incident.resolved',
])

function parseRealtimeEvent(
    payload: string,
): RealtimeEvent | null {
    try {
        const parsed: unknown = JSON.parse(payload)

        if (typeof parsed !== 'object' || parsed === null) {
            return null
        }

        const candidate = parsed as Partial<RealtimeEvent>

        if (
            typeof candidate.event_id !== 'string' ||
            typeof candidate.type !== 'string' ||
            !realtimeEventTypes.has(
                candidate.type as RealtimeEventType,
            ) ||
            typeof candidate.monitor_id !== 'string' ||
            typeof candidate.check_id !== 'number'
        ) {
            return null
        }

        return candidate as RealtimeEvent
    } catch {
        return null
    }
}

export function RealtimeProvider({
    children,
}: PropsWithChildren) {
    const { status, user } = useAuth()
    const queryClient = useQueryClient()
    const reconnectAttempt = useRef(0)

    useEffect(() => {
        if (status !== 'authenticated') {
            return
        }

        let disposed = false
        let socket: WebSocket | null = null
        let reconnectTimer: number | null = null

        function invalidateQueries(event: RealtimeEvent) {
            const invalidations = [
                queryClient.invalidateQueries({
                    queryKey: dashboardKeys.summary,
                    exact: true,
                }),
                queryClient.invalidateQueries({
                    queryKey: monitorKeys.all,
                    exact: true,
                }),
                queryClient.invalidateQueries({
                    queryKey: monitorKeys.detail(
                        event.monitor_id,
                    ),
                    exact: true,
                }),
                queryClient.invalidateQueries({
                    queryKey: monitorKeys.checks(
                        event.monitor_id,
                    ),
                }),
                queryClient.invalidateQueries({
                    queryKey: [
                        'monitors',
                        event.monitor_id,
                        'metrics',
                    ],
                }),
            ]

            if (event.type.startsWith('incident.')) {
                invalidations.push(
                    queryClient.invalidateQueries({
                        queryKey: incidentKeys.all,
                    }),
                )
            }

            void Promise.all(invalidations)
        }

        function scheduleReconnect() {
            if (disposed || reconnectTimer !== null) {
                return
            }

            const delay = Math.min(
                INITIAL_RECONNECT_DELAY_MS *
                2 ** reconnectAttempt.current,
                MAX_RECONNECT_DELAY_MS,
            )
            reconnectAttempt.current += 1

            reconnectTimer = window.setTimeout(() => {
                reconnectTimer = null
                void connect()
            }, delay)
        }

        async function connect() {
            try {
                const { ticket } = await issueRealtimeTicket()

                if (disposed) {
                    return
                }

                const currentSocket =
                    createRealtimeSocket(ticket)
                socket = currentSocket

                currentSocket.onopen = () => {
                    reconnectAttempt.current = 0
                }

                currentSocket.onmessage = (message) => {
                    if (typeof message.data !== 'string') {
                        return
                    }

                    const event = parseRealtimeEvent(
                        message.data,
                    )

                    if (event !== null) {
                        invalidateQueries(event)
                    }
                }

                currentSocket.onerror = () => {
                    currentSocket.close()
                }

                currentSocket.onclose = () => {
                    if (socket === currentSocket) {
                        socket = null
                    }

                    scheduleReconnect()
                }
            } catch {
                scheduleReconnect()
            }
        }

        void connect()

        return () => {
            disposed = true

            if (reconnectTimer !== null) {
                window.clearTimeout(reconnectTimer)
            }

            socket?.close(1000, 'Session ended')
            socket = null
        }
    }, [queryClient, status, user?.id])

    return children
}