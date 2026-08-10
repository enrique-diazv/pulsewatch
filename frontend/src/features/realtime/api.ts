import {
    apiRequest,
    buildWebSocketUrl,
} from '../../services/api/client.ts'
import type { RealtimeTicketResponse } from './types.ts'

export function issueRealtimeTicket() {
    return apiRequest<RealtimeTicketResponse>(
        '/realtime/ticket',
        {
            authenticated: true,
            method: 'POST',
        },
    )
}

export function createRealtimeSocket(
    ticket: string,
): WebSocket {
    const url = buildWebSocketUrl('/realtime/ws')

    url.searchParams.set('ticket', ticket)

    return new WebSocket(url)
}