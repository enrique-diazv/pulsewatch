import { describe, expect, it } from 'vitest'

import {
    loginSchema,
    registerSchema,
} from './schemas.ts'

describe('loginSchema', () => {
    it('accepts valid credentials', () => {
        const result = loginSchema.safeParse({
            email: 'user@example.com',
            password: 'password',
        })

        expect(result.success).toBe(true)
    })

    it('rejects an invalid email', () => {
        const result = loginSchema.safeParse({
            email: 'invalid-email',
            password: 'password',
        })

        expect(result.success).toBe(false)
    })
})

describe('registerSchema', () => {
    it('accepts matching secure passwords', () => {
        const result = registerSchema.safeParse({
            email: 'user@example.com',
            password: 'correct horse battery staple',
            confirmPassword: 'correct horse battery staple',
        })

        expect(result.success).toBe(true)
    })

    it('rejects mismatched passwords', () => {
        const result = registerSchema.safeParse({
            email: 'user@example.com',
            password: 'correct horse battery staple',
            confirmPassword: 'different secure password',
        })

        expect(result.success).toBe(false)
    })
})

it('accepts a six-character password', () => {
    const result = registerSchema.safeParse({
        email: 'user@example.com',
        password: 'secret',
        confirmPassword: 'secret',
    })

    expect(result.success).toBe(true)
})

it('rejects passwords shorter than six characters', () => {
    const result = registerSchema.safeParse({
        email: 'user@example.com',
        password: 'short',
        confirmPassword: 'short',
    })

    expect(result.success).toBe(false)
})