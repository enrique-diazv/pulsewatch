import http from 'k6/http'
import {
    check,
    fail,
    sleep,
} from 'k6'

const baseUrl =
    __ENV.K6_BASE_URL ??
    'http://127.0.0.1:8000/api/v1'

const email = __ENV.K6_EMAIL
const password = __ENV.K6_PASSWORD
const monitorId = __ENV.K6_MONITOR_ID

export const options = {
    summaryTrendStats: [
        'avg',
        'min',
        'p(50)',
        'p(90)',
        'p(95)',
        'p(99)',
        'max',
    ],
    stages: [
        {
            duration: '20s',
            target: 10,
        },
        {
            duration: '1m',
            target: 10,
        },
        {
            duration: '20s',
            target: 25,
        },
        {
            duration: '1m',
            target: 25,
        },
        {
            duration: '20s',
            target: 0,
        },
    ],
    thresholds: {
        http_req_failed: ['rate<0.01'],
        'http_req_duration{name:dashboard_summary}': [
            'p(95)<300',
        ],
        'http_req_duration{name:list_monitors}': [
            'p(95)<300',
        ],
        'http_req_duration{name:monitor_metrics}': [
            'p(95)<300',
        ],
        'http_req_duration{name:monitor_checks}': [
            'p(95)<400',
        ],
    },
}

export function setup() {
    if (!email || !password || !monitorId) {
        fail(
            'K6_EMAIL, K6_PASSWORD and K6_MONITOR_ID are required',
        )
    }

    const response = http.post(
        `${baseUrl}/auth/login`,
        JSON.stringify({
            email,
            password,
        }),
        {
            headers: {
                'Content-Type': 'application/json',
            },
            tags: {
                name: 'auth_login_setup',
            },
        },
    )

    const authenticated = check(response, {
        'login returns 200': (result) =>
            result.status === 200,
    })

    if (!authenticated) {
        fail(
            `Login failed with status ${response.status}`,
        )
    }

    return {
        accessToken: response.json('access_token'),
    }
}

export default function (data) {
    const authenticatedHeaders = {
        Authorization: `Bearer ${data.accessToken}`,
    }
    const selection = Math.random()
    let response
    let accepted

    if (selection < 0.2) {
        response = http.get(
            `${baseUrl}/dashboard/summary`,
            {
                headers: authenticatedHeaders,
                tags: {
                    name: 'dashboard_summary',
                },
            },
        )
        accepted = response.status === 200
    } else if (selection < 0.4) {
        response = http.get(
            `${baseUrl}/monitors`,
            {
                headers: authenticatedHeaders,
                tags: {
                    name: 'list_monitors',
                },
            },
        )
        accepted = response.status === 200
    } else if (selection < 0.55) {
        response = http.get(
            `${baseUrl}/monitors/${monitorId}/metrics?range=24h`,
            {
                headers: authenticatedHeaders,
                tags: {
                    name: 'monitor_metrics',
                },
            },
        )
        accepted = response.status === 200
    } else if (selection < 0.7) {
        response = http.get(
            `${baseUrl}/monitors/${monitorId}/checks?limit=50`,
            {
                headers: authenticatedHeaders,
                tags: {
                    name: 'monitor_checks',
                },
            },
        )
        accepted = response.status === 200
    } else if (selection < 0.85) {
        response = http.patch(
            `${baseUrl}/monitors/${monitorId}`,
            JSON.stringify({
                name: 'k6 Load Test Monitor',
            }),
            {
                headers: {
                    ...authenticatedHeaders,
                    'Content-Type': 'application/json',
                },
                tags: {
                    name: 'update_monitor',
                },
            },
        )
        accepted = response.status === 200
    } else if (selection < 0.9) {
        response = http.post(
            `${baseUrl}/monitors/${monitorId}/check`,
            null,
            {
                headers: authenticatedHeaders,
                responseCallback: http.expectedStatuses(
                    202,
                    429,
                ),
                tags: {
                    name: 'manual_check',
                },
            },
        )
        accepted =
            response.status === 202 ||
            response.status === 429
    } else {
        response = http.post(
            `${baseUrl}/auth/login`,
            JSON.stringify({
                email,
                password,
            }),
            {
                headers: {
                    'Content-Type': 'application/json',
                },
                tags: {
                    name: 'auth_login',
                },
            },
        )
        accepted = response.status === 200
    }

    check(response, {
        'mixed request returns expected status': () =>
            accepted,
    })

    sleep(1)
}