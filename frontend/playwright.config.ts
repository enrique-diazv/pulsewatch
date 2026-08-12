import {
    defineConfig,
    devices,
} from '@playwright/test'

const pythonExecutable =
    process.platform === 'win32'
        ? '.\\.venv\\Scripts\\python.exe'
        : 'python'

const npmExecutable =
    process.platform === 'win32'
        ? 'npm.cmd'
        : 'npm'

export default defineConfig({
    testDir: './e2e',
    fullyParallel: true,
    forbidOnly: Boolean(process.env.CI),
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: [
        ['list'],
        ['html', { open: 'never' }],
    ],
    use: {
        baseURL: 'http://localhost:5173',
        trace: 'retain-on-failure',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
    },
    projects: [
        {
            name: 'chromium',
            use: {
                ...devices['Desktop Chrome'],
            },
        },
    ],
    webServer: [
        {
            command: [
                pythonExecutable,
                '-m uvicorn app.main:app',
                '--host 127.0.0.1',
                '--port 8000',
            ].join(' '),
            cwd: '../backend',
            url: 'http://127.0.0.1:8000/health',
            reuseExistingServer: !process.env.CI,
            timeout: 120_000,
        },
        {
            command: [
                npmExecutable,
                'run dev',
                '-- --host localhost',
            ].join(' '),
            url: 'http://localhost:5173',
            reuseExistingServer: !process.env.CI,
            timeout: 120_000,
        },
    ],
})