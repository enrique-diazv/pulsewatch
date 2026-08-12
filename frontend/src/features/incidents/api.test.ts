import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import { apiRequest } from '../../services/api/client.ts'
import {
    getIncident,
    listIncidents,
} from './api.ts'

vi.mock('../../services/api/client.ts')

const mockedApiRequest = vi.mocked(apiRequest)

beforeEach(() => {
    vi.resetAllMocks()
    mockedApiRequest.mockResolvedValue(undefined)
})

describe('incident API', () => {
    it('lists all incidents without a filter', async () => {
        await listIncidents()

        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/incidents',
            {
                authenticated: true,
            },
        )
    })

    it('lists incidents using a status filter', async () => {
        await listIncidents('RESOLVED')

        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/incidents?status=RESOLVED',
            {
                authenticated: true,
            },
        )
    })

    it('gets an incident by id', async () => {
        await getIncident('incident-123')

        expect(mockedApiRequest).toHaveBeenCalledWith(
            '/incidents/incident-123',
            {
                authenticated: true,
            },
        )
    })
})