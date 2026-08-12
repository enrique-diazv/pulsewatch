import {
    render,
    screen,
} from '@testing-library/react'
import {
    MemoryRouter,
    Route,
    Routes,
} from 'react-router-dom'
import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import type { AuthStatus } from '../../features/auth/context.ts'
import { useAuth } from '../../features/auth/useAuth.ts'
import { ProtectedRoute } from './ProtectedRoute.tsx'
import { PublicOnlyRoute } from './PublicOnlyRoute.tsx'

vi.mock('../../features/auth/useAuth.ts')

const mockedUseAuth = vi.mocked(useAuth)

function setAuthStatus(status: AuthStatus) {
    mockedUseAuth.mockReturnValue({
        user: null,
        status,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
    })
}

function renderProtectedRoute() {
    return render(
        <MemoryRouter initialEntries={['/private']}>
            <Routes>
                <Route element={<ProtectedRoute />}>
                    <Route
                        element={<h1>Private workspace</h1>}
                        path="/private"
                    />
                </Route>
                <Route
                    element={<h1>Login page</h1>}
                    path="/login"
                />
            </Routes>
        </MemoryRouter>,
    )
}

function renderPublicRoute() {
    return render(
        <MemoryRouter initialEntries={['/login']}>
            <Routes>
                <Route element={<PublicOnlyRoute />}>
                    <Route
                        element={<h1>Login page</h1>}
                        path="/login"
                    />
                </Route>
                <Route
                    element={<h1>Dashboard page</h1>}
                    path="/dashboard"
                />
            </Routes>
        </MemoryRouter>,
    )
}

beforeEach(() => {
    vi.resetAllMocks()
})

describe('ProtectedRoute', () => {
    it('shows the session loader while restoring', () => {
        setAuthStatus('loading')

        renderProtectedRoute()

        expect(
            screen.getByText(/Restoring your session/),
        ).toBeVisible()
    })

    it('redirects anonymous users to login', () => {
        setAuthStatus('anonymous')

        renderProtectedRoute()

        expect(
            screen.getByRole('heading', {
                name: 'Login page',
            }),
        ).toBeVisible()
    })

    it('renders protected content for authenticated users', () => {
        setAuthStatus('authenticated')

        renderProtectedRoute()

        expect(
            screen.getByRole('heading', {
                name: 'Private workspace',
            }),
        ).toBeVisible()
    })
})

describe('PublicOnlyRoute', () => {
    it('shows the session loader while restoring', () => {
        setAuthStatus('loading')

        renderPublicRoute()

        expect(
            screen.getByText(/Restoring your session/),
        ).toBeVisible()
    })

    it('renders public content for anonymous users', () => {
        setAuthStatus('anonymous')

        renderPublicRoute()

        expect(
            screen.getByRole('heading', {
                name: 'Login page',
            }),
        ).toBeVisible()
    })

    it('redirects authenticated users to the dashboard', () => {
        setAuthStatus('authenticated')

        renderPublicRoute()

        expect(
            screen.getByRole('heading', {
                name: 'Dashboard page',
            }),
        ).toBeVisible()
    })
})