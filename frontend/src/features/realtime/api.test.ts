import {
    afterEach,
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import {
    apiRequest,
    buildWebSocketUrl,
} from '../../services/api/client.ts'
import {
    createRealtimeSocket,
    issueRealtimeTicket,
} from './api.ts'

vi.mock('../../services/api/client.ts')

const mockedApiRequest = vi.mocked(apiRequest)
const mockedBuildWebSocketUrl =
    vi.mocked(buildWebSocketUrl)
const websocketConstructor = vi.fn()

beforeEach(() => {
    vi.resetAllMocks()
    vi.stubGlobal(
        'WebSocket',
        websocketConstructor,
    )
})

afterEach(() => {
    vi.unstubAllGlobals()
})

describe('realtime API', () => {
    it('requests a single-use connection ticket', async () => {
        mockedApiRequest.mockResolvedValue({
            ticket: 'ticket-123',
            expires_in: 30,
        })

        await issueRealtimeTicket()

        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/realtime/ticket',
            {
                authenticated: true,
                method: 'POST',
            },
        )
    })

    it('creates a WebSocket with an encoded ticket', () => {
        const ticket = 'ticket with spaces&symbols'
        mockedBuildWebSocketUrl.mockReturnValue(
            new URL(
                'ws://localhost:8000/api/v1/realtime/ws',
            ),
        )

        createRealtimeSocket(ticket)

        expect(
            mockedBuildWebSocketUrl,
        ).toHaveBeenCalledWith('/realtime/ws')
        expect(
            websocketConstructor,
        ).toHaveBeenCalledOnce()

        const websocketUrl =
            websocketConstructor.mock.calls[0][0]

        expect(websocketUrl).toBeInstanceOf(URL)
        expect(websocketUrl.searchParams.get('ticket')).toBe(
            ticket,
        )
    })
})