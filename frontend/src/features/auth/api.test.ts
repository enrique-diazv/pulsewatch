import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import {
    apiRequest,
    clearAccessToken,
    setAccessToken,
} from '../../services/api/client.ts'
import {
    loginUser,
    logoutUser,
    refreshAccessToken,
    registerUser,
    restoreUserSession,
} from './api.ts'
import type {
    AccessTokenResponse,
    User,
} from './types.ts'

vi.mock('../../services/api/client.ts')

const mockedApiRequest = vi.mocked(apiRequest)
const mockedSetAccessToken = vi.mocked(setAccessToken)
const mockedClearAccessToken =
    vi.mocked(clearAccessToken)

const user: User = {
    id: 'user-123',
    email: 'owner@example.com',
    is_verified: true,
    created_at: '2026-08-12T00:00:00Z',
    updated_at: '2026-08-12T00:00:00Z',
}

const token: AccessTokenResponse = {
    access_token: 'access-token',
    token_type: 'bearer',
    expires_in: 900,
}

const credentials = {
    email: user.email,
    password: 'secret-password',
}

beforeEach(() => {
    vi.resetAllMocks()
})

describe('authentication API', () => {
    it('registers a user', async () => {
        mockedApiRequest.mockResolvedValue(user)

        const result = await registerUser(credentials)

        expect(result).toEqual(user)
        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/auth/register',
            {
                method: 'POST',
                json: credentials,
            },
        )
    })

    it('stores the access token after login', async () => {
        mockedApiRequest.mockResolvedValue(token)

        const result = await loginUser(credentials)

        expect(result).toEqual(token)
        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/auth/login',
            {
                method: 'POST',
                json: credentials,
            },
        )
        expect(mockedSetAccessToken).toHaveBeenCalledWith(
            token.access_token,
        )
    })

    it('stores a refreshed access token', async () => {
        mockedApiRequest.mockResolvedValue(token)

        const result = await refreshAccessToken()

        expect(result).toEqual(token)
        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/auth/refresh',
            {
                method: 'POST',
            },
        )
        expect(mockedSetAccessToken).toHaveBeenCalledWith(
            token.access_token,
        )
    })

    it('deduplicates concurrent session restoration', async () => {
        mockedApiRequest
            .mockResolvedValueOnce(token)
            .mockResolvedValueOnce(user)

        const firstRestoration = restoreUserSession()
        const secondRestoration = restoreUserSession()

        expect(firstRestoration).toBe(secondRestoration)
        await expect(firstRestoration).resolves.toEqual(user)

        expect(mockedApiRequest).toHaveBeenNthCalledWith(
            1,
            '/auth/refresh',
            {
                method: 'POST',
            },
        )
        expect(mockedApiRequest).toHaveBeenNthCalledWith(
            2,
            '/auth/me',
            {
                authenticated: true,
            },
        )
    })

    it('clears the token after logout', async () => {
        mockedApiRequest.mockResolvedValue(undefined)

        await logoutUser()

        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/auth/logout',
            {
                method: 'POST',
            },
        )
        expect(mockedClearAccessToken).toHaveBeenCalledOnce()
    })

    it('clears the token when logout fails', async () => {
        mockedApiRequest.mockRejectedValue(
            new Error('Network unavailable'),
        )

        await expect(logoutUser()).rejects.toThrow(
            'Network unavailable',
        )

        expect(mockedClearAccessToken).toHaveBeenCalledOnce()
    })
})