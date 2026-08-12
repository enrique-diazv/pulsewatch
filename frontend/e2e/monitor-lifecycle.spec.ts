import {
    expect,
    test,
} from '@playwright/test'

test('registers and manages a monitor', async ({
    page,
}, testInfo) => {
    const suffix = `${Date.now()}-${testInfo.workerIndex}`
    const email = `e2e-${suffix}@example.com`
    const password = 'pulsewatch-e2e-password'
    const monitorName = `E2E Monitor ${suffix}`

    await page.goto('/register')

    await page.getByLabel('Email address').fill(email)
    await page.getByLabel('Password', {
        exact: true,
    }).fill(password)
    await page.getByLabel('Confirm password').fill(password)
    await page.getByRole('button', {
        name: 'Create account',
    }).click()

    await expect(page).toHaveURL('/dashboard')
    await expect(
        page.getByRole('heading', {
            name: 'Dashboard',
        }),
    ).toBeVisible()

    await page.getByRole('link', {
        name: 'Add monitor',
    }).click()

    await page.getByLabel('Monitor name').fill(monitorName)
    await page.getByLabel('URL').fill(
        'https://example.com/',
    )
    await page.getByRole('button', {
        name: 'Create monitor',
    }).click()

    await expect(page).toHaveURL('/monitors')
    await page.getByRole('link', {
        name: monitorName,
    }).click()

    await expect(
        page.getByRole('heading', {
            name: monitorName,
        }),
    ).toBeVisible()

    await page.getByRole('button', {
        name: 'Pause',
    }).click()

    await expect(
        page.getByText('Monitor paused.'),
    ).toBeVisible()
    await expect(
        page.getByRole('button', {
            name: 'Resume',
        }),
    ).toBeVisible()

    await page.getByRole('button', {
        name: 'Resume',
    }).click()

    await expect(
        page.getByText(
            'Monitor resumed and scheduled.',
        ),
    ).toBeVisible()

    await page.getByRole('button', {
        name: 'Delete',
    }).click()

    const dialog = page.getByRole('dialog')

    await expect(dialog).toBeVisible()
    await dialog.getByRole('button', {
        name: 'Delete monitor',
    }).click()

    await expect(page).toHaveURL('/monitors')
    await expect(
        page.getByRole('link', {
            name: monitorName,
        }),
    ).toHaveCount(0)

    await page.getByRole('button', {
        name: 'Sign out',
    }).click()

    await expect(page).toHaveURL('/login')
})