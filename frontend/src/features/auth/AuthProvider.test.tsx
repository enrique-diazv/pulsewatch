import {
    fireEvent,
    render,
    screen,
    waitFor,
} from '@testing-library/react'
import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import { clearAccessToken } from '../../services/api/client.ts'
import {
    getCurrentUser,
    loginUser,
    logoutUser,
    registerUser,
    restoreUserSession,
} from './api.ts'
import { AuthProvider } from './AuthProvider.tsx'
import type { User } from './types.ts'
import { useAuth } from './useAuth.ts'

vi.mock('./api.ts')
vi.mock('../../services/api/client.ts', () => ({
    clearAccessToken: vi.fn(),
}))

const mockedRestoreUserSession =
    vi.mocked(restoreUserSession)
const mockedLoginUser = vi.mocked(loginUser)
const mockedRegisterUser = vi.mocked(registerUser)
const mockedGetCurrentUser = vi.mocked(getCurrentUser)
const mockedLogoutUser = vi.mocked(logoutUser)
const mockedClearAccessToken =
    vi.mocked(clearAccessToken)

const user: User = {
    id: 'user-123',
    email: 'owner@example.com',
    is_verified: true,
    created_at: '2026-08-12T00:00:00Z',
    updated_at: '2026-08-12T00:00:00Z',
}

const credentials = {
    email: user.email,
    password: 'secret-password',
}

function AuthConsumer() {
    const {
        user: currentUser,
        status,
        login,
        register,
        logout,
    } = useAuth()

    return (
        <div>
            <span data-testid="status">{status}</span>
            <span data-testid="email">
                {currentUser?.email ?? 'No user'}
            </span>

            <button
                onClick={() => {
                    void login(credentials)
                }}
                type="button"
            >
                Log in
            </button>

            <button
                onClick={() => {
                    void register(credentials)
                }}
                type="button"
            >
                Register
            </button>

            <button
                onClick={() => {
                    void logout().catch(() => undefined)
                }}
                type="button"
            >
                Log out
            </button>
        </div>
    )
}

function renderProvider() {
    return render(
        <AuthProvider>
            <AuthConsumer />
        </AuthProvider>,
    )
}

beforeEach(() => {
    vi.resetAllMocks()
})

describe('AuthProvider', () => {
    it('restores an authenticated session', async () => {
        mockedRestoreUserSession.mockResolvedValue(user)

        renderProvider()

        expect(
            screen.getByTestId('status'),
        ).toHaveTextContent('loading')

        await waitFor(() => {
            expect(
                screen.getByTestId('status'),
            ).toHaveTextContent('authenticated')
        })

        expect(
            screen.getByTestId('email'),
        ).toHaveTextContent(user.email)
    })

    it('clears an invalid restored session', async () => {
        mockedRestoreUserSession.mockRejectedValue(
            new Error('Refresh token expired'),
        )

        renderProvider()

        await waitFor(() => {
            expect(
                screen.getByTestId('status'),
            ).toHaveTextContent('anonymous')
        })

        expect(mockedClearAccessToken).toHaveBeenCalledOnce()
        expect(
            screen.getByTestId('email'),
        ).toHaveTextContent('No user')
    })

    it('logs in and loads the current user', async () => {
        mockedRestoreUserSession.mockRejectedValue(
            new Error('No session'),
        )
        mockedLoginUser.mockResolvedValue({
            access_token: 'access-token',
            token_type: 'bearer',
            expires_in: 900,
        })
        mockedGetCurrentUser.mockResolvedValue(user)

        renderProvider()

        await waitFor(() => {
            expect(
                screen.getByTestId('status'),
            ).toHaveTextContent('anonymous')
        })

        fireEvent.click(
            screen.getByRole('button', {
                name: 'Log in',
            }),
        )

        await waitFor(() => {
            expect(
                screen.getByTestId('status'),
            ).toHaveTextContent('authenticated')
        })

        expect(mockedLoginUser).toHaveBeenCalledWith(
            credentials,
        )
        expect(mockedGetCurrentUser).toHaveBeenCalledOnce()
    })

    it('registers, authenticates, and logs out', async () => {
        mockedRestoreUserSession.mockRejectedValue(
            new Error('No session'),
        )
        mockedRegisterUser.mockResolvedValue(user)
        mockedLoginUser.mockResolvedValue({
            access_token: 'access-token',
            token_type: 'bearer',
            expires_in: 900,
        })
        mockedGetCurrentUser.mockResolvedValue(user)
        mockedLogoutUser.mockResolvedValue()

        renderProvider()

        await waitFor(() => {
            expect(
                screen.getByTestId('status'),
            ).toHaveTextContent('anonymous')
        })

        fireEvent.click(
            screen.getByRole('button', {
                name: 'Register',
            }),
        )

        await waitFor(() => {
            expect(
                screen.getByTestId('status'),
            ).toHaveTextContent('authenticated')
        })

        expect(mockedRegisterUser).toHaveBeenCalledWith(
            credentials,
        )
        expect(mockedLoginUser).toHaveBeenCalledWith(
            credentials,
        )

        fireEvent.click(
            screen.getByRole('button', {
                name: 'Log out',
            }),
        )

        await waitFor(() => {
            expect(
                screen.getByTestId('status'),
            ).toHaveTextContent('anonymous')
        })

        expect(mockedLogoutUser).toHaveBeenCalledOnce()
        expect(
            screen.getByTestId('email'),
        ).toHaveTextContent('No user')
    })
})