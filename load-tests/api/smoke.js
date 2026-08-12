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
            duration: '10s',
            target: 5,
        },
        {
            duration: '30s',
            target: 5,
        },
        {
            duration: '10s',
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
    const requestOptions = {
        headers: {
            Authorization: `Bearer ${data.accessToken}`,
        },
    }
    const selection = Math.random()
    let response

    if (selection < 0.25) {
        response = http.get(
            `${baseUrl}/dashboard/summary`,
            {
                ...requestOptions,
                tags: {
                    name: 'dashboard_summary',
                },
            },
        )
    } else if (selection < 0.5) {
        response = http.get(
            `${baseUrl}/monitors`,
            {
                ...requestOptions,
                tags: {
                    name: 'list_monitors',
                },
            },
        )
    } else if (selection < 0.75) {
        response = http.get(
            `${baseUrl}/monitors/${monitorId}/metrics?range=24h`,
            {
                ...requestOptions,
                tags: {
                    name: 'monitor_metrics',
                },
            },
        )
    } else {
        response = http.get(
            `${baseUrl}/monitors/${monitorId}/checks?limit=50`,
            {
                ...requestOptions,
                tags: {
                    name: 'monitor_checks',
                },
            },
        )
    }

    check(response, {
        'read request returns 200': (result) =>
            result.status === 200,
    })

    sleep(1)
}