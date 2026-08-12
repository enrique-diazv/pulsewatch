import {
    render,
    screen,
    within,
} from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import { useDashboardSummary } from '../features/dashboard/queries.ts'
import type { DashboardSummary } from '../features/dashboard/types.ts'
import { useMonitors } from '../features/monitors/queries.ts'
import type { Monitor } from '../features/monitors/types.ts'
import { DashboardPage } from './DashboardPage.tsx'

vi.mock('../features/dashboard/queries.ts')
vi.mock('../features/monitors/queries.ts')

const mockedUseDashboardSummary = vi.mocked(
    useDashboardSummary,
)
const mockedUseMonitors = vi.mocked(useMonitors)

const monitor: Monitor = {
    id: 'monitor-123',
    name: 'Production API',
    url: 'https://api.example.com/health',
    method: 'GET',
    interval_seconds: 60,
    timeout_seconds: 5,
    expected_status: 200,
    status: 'UP',
    failure_threshold: 3,
    recovery_threshold: 2,
    is_active: true,
    last_checked_at: '2026-08-12T01:00:00Z',
    next_check_at: '2026-08-12T01:01:00Z',
    created_at: '2026-08-12T00:00:00Z',
    updated_at: '2026-08-12T01:00:00Z',
}

const summary: DashboardSummary = {
    total_monitors: 12,
    operational_monitors: 10,
    down_monitors: 1,
    degraded_monitors: 1,
    active_incidents: 1,
    total_checks: 1000,
    successful_checks: 998,
    overall_uptime_percentage: 99.8,
    average_response_time_ms: 184.5,
}

function renderPage() {
    return render(
        <MemoryRouter>
            <DashboardPage />
        </MemoryRouter>,
    )
}

beforeEach(() => {
    vi.resetAllMocks()

    mockedUseMonitors.mockReturnValue({
        data: [monitor],
        isPending: false,
        isError: false,
    } as ReturnType<typeof useMonitors>)

    mockedUseDashboardSummary.mockReturnValue({
        data: summary,
        isPending: false,
        isError: false,
    } as ReturnType<typeof useDashboardSummary>)
})

describe('DashboardPage', () => {
    it('renders cached summary metrics and monitor snapshot', () => {
        renderPage()

        const totalCard = screen
            .getByText('Total monitors')
            .closest('article')
        const uptimeCard = screen
            .getByText('Overall uptime')
            .closest('article')
        const responseCard = screen
            .getByText('Average response')
            .closest('article')

        expect(totalCard).not.toBeNull()
        expect(uptimeCard).not.toBeNull()
        expect(responseCard).not.toBeNull()

        expect(
            within(totalCard!).getByText('12'),
        ).toBeVisible()
        expect(
            within(uptimeCard!).getByText('99.80%'),
        ).toBeVisible()
        expect(
            within(responseCard!).getByText('185 ms'),
        ).toBeVisible()
        expect(
            screen.getByText('Production API'),
        ).toBeVisible()
    })

    it('waits for the summary query', () => {
        mockedUseDashboardSummary.mockReturnValue({
            data: undefined,
            isPending: true,
            isError: false,
        } as ReturnType<typeof useDashboardSummary>)

        renderPage()

        expect(
            screen.getByText('Loading dashboard...'),
        ).toBeVisible()
    })
})