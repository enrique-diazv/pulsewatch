import {
    QueryClient,
    QueryClientProvider,
} from '@tanstack/react-query'
import {
    act,
    render,
    waitFor,
} from '@testing-library/react'
import type { PropsWithChildren } from 'react'
import {
    afterEach,
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import { useAuth } from '../auth/useAuth.ts'
import {
    createRealtimeSocket,
    issueRealtimeTicket,
} from './api.ts'
import { RealtimeProvider } from './RealtimeProvider.tsx'

vi.mock('../auth/useAuth.ts')
vi.mock('./api.ts')

const mockedUseAuth = vi.mocked(useAuth)
const mockedIssueRealtimeTicket =
    vi.mocked(issueRealtimeTicket)
const mockedCreateRealtimeSocket =
    vi.mocked(createRealtimeSocket)

function createSocket(): WebSocket {
    return {
        onopen: null,
        onmessage: null,
        onerror: null,
        onclose: null,
        close: vi.fn(),
    } as unknown as WebSocket
}

function setAuthenticatedUser() {
    mockedUseAuth.mockReturnValue({
        user: {
            id: 'user-123',
            email: 'owner@example.com',
            is_verified: true,
            created_at: '2026-08-10T00:00:00Z',
            updated_at: '2026-08-10T00:00:00Z',
        },
        status: 'authenticated',
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
    })
}

function renderProvider() {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    })

    function Wrapper({ children }: PropsWithChildren) {
        return (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )
    }

    const rendered = render(
        <RealtimeProvider>
            <div>Application</div>
        </RealtimeProvider>,
        { wrapper: Wrapper },
    )

    return {
        ...rendered,
        queryClient,
    }
}

beforeEach(() => {
    vi.resetAllMocks()
    setAuthenticatedUser()
    mockedIssueRealtimeTicket.mockResolvedValue({
        ticket: 'realtime-ticket',
        expires_in: 30,
    })
})

afterEach(() => {
    vi.useRealTimers()
})

describe('RealtimeProvider', () => {
    it('connects and invalidates affected queries', async () => {
        const socket = createSocket()

        mockedCreateRealtimeSocket.mockReturnValue(socket)

        const { queryClient } = renderProvider()
        const invalidateQueries = vi.spyOn(
            queryClient,
            'invalidateQueries',
        )

        await waitFor(() => {
            expect(
                mockedCreateRealtimeSocket,
            ).toHaveBeenCalledWith('realtime-ticket')
        })

        act(() => {
            socket.onmessage?.(
                new MessageEvent('message', {
                    data: JSON.stringify({
                        event_id: 'event-123',
                        type: 'incident.opened',
                        occurred_at: '2026-08-10T00:00:00Z',
                        monitor_id: 'monitor-123',
                        monitor_status: 'DOWN',
                        check_id: 321,
                        incident_id: 'incident-123',
                    }),
                }),
            )
        })
        await waitFor(() => {
            expect(invalidateQueries).toHaveBeenCalledWith({
                queryKey: ['dashboard', 'summary'],
                exact: true,
            })
            expect(invalidateQueries).toHaveBeenCalledWith({
                queryKey: ['monitors'],
                exact: true,
            })
            expect(invalidateQueries).toHaveBeenCalledWith({
                queryKey: [
                    'monitors',
                    'monitor-123',
                    'checks',
                ],
            })
            expect(invalidateQueries).toHaveBeenCalledWith({
                queryKey: ['incidents'],
            })
        })
        await waitFor(() => {
            expect(invalidateQueries).toHaveBeenCalledWith({
                queryKey: ['monitors'],
                exact: true,
            })
            expect(invalidateQueries).toHaveBeenCalledWith({
                queryKey: [
                    'monitors',
                    'monitor-123',
                    'checks',
                ],
            })
            expect(invalidateQueries).toHaveBeenCalledWith({
                queryKey: ['incidents'],
            })
        })
    })

    it('does not connect for an anonymous session', () => {
        mockedUseAuth.mockReturnValue({
            user: null,
            status: 'anonymous',
            login: vi.fn(),
            register: vi.fn(),
            logout: vi.fn(),
        })

        renderProvider()

        expect(
            mockedIssueRealtimeTicket,
        ).not.toHaveBeenCalled()
        expect(
            mockedCreateRealtimeSocket,
        ).not.toHaveBeenCalled()
    })

    it('requests a new ticket after disconnection', async () => {
        vi.useFakeTimers()

        const firstSocket = createSocket()
        const secondSocket = createSocket()

        mockedCreateRealtimeSocket
            .mockReturnValueOnce(firstSocket)
            .mockReturnValueOnce(secondSocket)

        const { unmount } = renderProvider()

        await act(async () => {
            await Promise.resolve()
            await Promise.resolve()
        })

        expect(
            mockedIssueRealtimeTicket,
        ).toHaveBeenCalledTimes(1)

        act(() => {
            firstSocket.onclose?.(
                new CloseEvent('close'),
            )
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(1_000)
        })

        expect(
            mockedIssueRealtimeTicket,
        ).toHaveBeenCalledTimes(2)
        expect(
            mockedCreateRealtimeSocket,
        ).toHaveBeenCalledTimes(2)

        unmount()
    })
})