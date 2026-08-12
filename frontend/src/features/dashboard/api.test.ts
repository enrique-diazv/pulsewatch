import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import { apiRequest } from '../../services/api/client.ts'
import { getDashboardSummary } from './api.ts'

vi.mock('../../services/api/client.ts')

const mockedApiRequest = vi.mocked(apiRequest)

beforeEach(() => {
    vi.resetAllMocks()
    mockedApiRequest.mockResolvedValue(undefined)
})

describe('dashboard API', () => {
    it('gets the authenticated dashboard summary', async () => {
        await getDashboardSummary()

        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/dashboard/summary',
            {
                authenticated: true,
            },
        )
    })
})