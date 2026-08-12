import {
    render,
    screen,
} from '@testing-library/react'
import {
    describe,
    expect,
    it,
} from 'vitest'

import type { MonitorStatus } from '../../features/monitors/types.ts'
import { MonitorStatusBadge } from './MonitorStatusBadge.tsx'

const statusCases: Array<{
    status: MonitorStatus
    label: string
}> = [
    {
        status: 'UP',
        label: 'Operational',
    },
    {
        status: 'DOWN',
        label: 'Down',
    },
    {
        status: 'DEGRADED',
        label: 'Degraded',
    },
    {
        status: 'PAUSED',
        label: 'Paused',
    },
    {
        status: 'UNKNOWN',
        label: 'Unknown',
    },
]

describe('MonitorStatusBadge', () => {
    it.each(statusCases)(
        'renders the accessible label for $status',
        ({ status, label }) => {
            render(
                <MonitorStatusBadge status={status} />,
            )

            const badge = screen.getByText(label)

            expect(badge).toBeVisible()
            expect(badge).toHaveClass(
                `status-badge--${status.toLowerCase()}`,
            )
        },
    )
})