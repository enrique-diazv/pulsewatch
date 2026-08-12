import {
    expect,
    test,
} from '@playwright/test'

test.describe('public authentication', () => {
    test('navigates between login and registration', async ({
        page,
    }) => {
        await page.goto('/login')

        await expect(
            page.getByRole('heading', {
                name: 'Welcome back',
            }),
        ).toBeVisible()

        await page.getByRole('link', {
            name: 'Create an account',
        }).click()

        await expect(page).toHaveURL('/register')
        await expect(
            page.getByRole('heading', {
                name: 'Create your account',
            }),
        ).toBeVisible()
    })

    test('shows accessible registration validation', async ({
        page,
    }) => {
        await page.goto('/register')

        await page.getByLabel('Email address').fill(
            'invalid-email',
        )
        await page.getByLabel('Password', {
            exact: true,
        }).fill('short')
        await page.getByLabel('Confirm password').fill(
            'different',
        )
        await page.getByRole('button', {
            name: 'Create account',
        }).click()

        await expect(
            page.getByText('Enter a valid email address'),
        ).toBeVisible()
        await expect(
            page.getByText(
                'Password must contain at least 6 characters',
            ),
        ).toBeVisible()
        await expect(
            page.getByText('Passwords do not match'),
        ).toBeVisible()
    })
})