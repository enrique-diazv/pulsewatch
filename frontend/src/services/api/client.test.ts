import {
    afterEach,
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import {
    ApiError,
    apiRequest,
    buildWebSocketUrl,
    clearAccessToken,
    setAccessToken,
} from './client.ts'

const fetchMock = vi.fn()

beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
    clearAccessToken()
})

afterEach(() => {
    vi.unstubAllGlobals()
})

describe('apiRequest', () => {
    it('sends authenticated JSON requests', async () => {
        fetchMock.mockResolvedValue(
            new Response(
                JSON.stringify({
                    id: 'monitor-123',
                }),
                {
                    status: 200,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                },
            ),
        )
        setAccessToken('access-token')

        const result = await apiRequest<{
            id: string
        }>('/monitors', {
            authenticated: true,
            method: 'POST',
            json: {
                name: 'Production API',
            },
        })

        expect(result).toEqual({
            id: 'monitor-123',
        })

        const [url, options] = fetchMock.mock.calls[0]
        const headers = new Headers(options.headers)

        expect(url).toBe(
            'http://localhost:8000/api/v1/monitors',
        )
        expect(options.method).toBe('POST')
        expect(options.credentials).toBe('include')
        expect(options.body).toBe(
            JSON.stringify({
                name: 'Production API',
            }),
        )
        expect(headers.get('Content-Type')).toBe(
            'application/json',
        )
        expect(headers.get('Authorization')).toBe(
            'Bearer access-token',
        )
    })

    it('does not send authorization after clearing the token', async () => {
        fetchMock.mockResolvedValue(
            new Response(
                JSON.stringify({
                    status: 'ok',
                }),
                {
                    status: 200,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                },
            ),
        )
        setAccessToken('temporary-token')
        clearAccessToken()

        await apiRequest('/health', {
            authenticated: true,
        })

        const [, options] = fetchMock.mock.calls[0]
        const headers = new Headers(options.headers)

        expect(headers.has('Authorization')).toBe(false)
    })

    it('returns undefined for an empty response', async () => {
        fetchMock.mockResolvedValue(
            new Response(null, {
                status: 204,
            }),
        )

        const result = await apiRequest<void>(
            '/auth/logout',
            {
                method: 'POST',
            },
        )

        expect(result).toBeUndefined()
    })

    it('throws an ApiError with the server detail', async () => {
        const payload = {
            detail: 'Monitor not found',
        }
        fetchMock.mockResolvedValue(
            new Response(
                JSON.stringify(payload),
                {
                    status: 404,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                },
            ),
        )

        await expect(
            apiRequest('/monitors/missing'),
        ).rejects.toMatchObject({
            name: 'ApiError',
            message: 'Monitor not found',
            status: 404,
            payload,
        } satisfies Partial<ApiError>)
    })

    it('uses a safe fallback for non-JSON errors', async () => {
        fetchMock.mockResolvedValue(
            new Response('Server unavailable', {
                status: 503,
                headers: {
                    'Content-Type': 'text/plain',
                },
            }),
        )

        await expect(
            apiRequest('/monitors'),
        ).rejects.toThrow(
            'The request could not be completed',
        )
    })
})

describe('buildWebSocketUrl', () => {
    it('converts the API URL to a WebSocket URL', () => {
        expect(
            buildWebSocketUrl('/realtime/ws').toString(),
        ).toBe(
            'ws://localhost:8000/api/v1/realtime/ws',
        )
    })
})