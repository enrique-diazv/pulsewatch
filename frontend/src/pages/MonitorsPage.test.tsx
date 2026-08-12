import {
    fireEvent,
    render,
    screen,
} from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import { useMonitors } from '../features/monitors/queries.ts'
import type { Monitor } from '../features/monitors/types.ts'
import { MonitorsPage } from './MonitorsPage.tsx'

vi.mock('../features/monitors/queries.ts')

const mockedUseMonitors = vi.mocked(useMonitors)

function setQueryResult(
    result: Partial<ReturnType<typeof useMonitors>>,
) {
    mockedUseMonitors.mockReturnValue(
        result as ReturnType<typeof useMonitors>,
    )
}

function renderPage() {
    return render(
        <MemoryRouter>
            <MonitorsPage />
        </MemoryRouter>,
    )
}

const monitor: Monitor = {
    id: 'monitor-123',
    name: 'Production API',
    url: 'https://api.example.com/health',
    method: 'GET',
    interval_seconds: 60,
    timeout_seconds: 5,
    expected_status: 200,
    status: 'UNKNOWN',
    failure_threshold: 3,
    recovery_threshold: 2,
    is_active: true,
    last_checked_at: null,
    next_check_at: '2026-08-12T01:00:00Z',
    created_at: '2026-08-12T00:00:00Z',
    updated_at: '2026-08-12T00:00:00Z',
}

beforeEach(() => {
    vi.resetAllMocks()
})

describe('MonitorsPage', () => {
    it('shows the loading state', () => {
        setQueryResult({
            data: undefined,
            isPending: true,
            isError: false,
        })

        renderPage()

        expect(
            screen.getByText(/Loading monitors/),
        ).toBeVisible()
    })

    it('shows an error and retries the query', () => {
        const refetch = vi.fn()

        setQueryResult({
            data: undefined,
            isPending: false,
            isError: true,
            refetch,
        })

        renderPage()

        expect(
            screen.getByRole('heading', {
                name: 'Unable to load monitors',
            }),
        ).toBeVisible()

        fireEvent.click(
            screen.getByRole('button', {
                name: 'Try again',
            }),
        )

        expect(refetch).toHaveBeenCalledOnce()
    })

    it('renders monitor information and status', () => {
        setQueryResult({
            data: [monitor],
            isPending: false,
            isError: false,
        })

        renderPage()

        expect(
            screen.getByRole('link', {
                name: 'Production API',
            }),
        ).toHaveAttribute(
            'href',
            '/monitors/monitor-123',
        )
        expect(
            screen.getByText(
                'https://api.example.com/health',
            ),
        ).toBeVisible()
        expect(
            screen.getByText('Unknown'),
        ).toBeVisible()
        expect(
            screen.getByText('Not checked yet'),
        ).toBeVisible()
    })
})