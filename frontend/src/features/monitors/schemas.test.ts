import { describe, expect, it } from 'vitest'

import { monitorCreateSchema } from './schemas.ts'

const validMonitor = {
  name: 'Production API',
  url: 'https://api.example.com/health',
  interval_seconds: 60,
  timeout_seconds: 5,
  expected_status: 200,
  failure_threshold: 3,
  recovery_threshold: 2,
}

describe('monitorCreateSchema', () => {
  it('accepts a valid HTTP monitor', () => {
    expect(
      monitorCreateSchema.safeParse(validMonitor).success,
    ).toBe(true)
  })

  it('rejects private file protocols', () => {
    expect(
      monitorCreateSchema.safeParse({
        ...validMonitor,
        url: 'file:///etc/passwd',
      }).success,
    ).toBe(false)
  })

  it('rejects intervals shorter than 30 seconds', () => {
    expect(
      monitorCreateSchema.safeParse({
        ...validMonitor,
        interval_seconds: 10,
      }).success,
    ).toBe(false)
  })

  it('rejects invalid HTTP status codes', () => {
    expect(
      monitorCreateSchema.safeParse({
        ...validMonitor,
        expected_status: 999,
      }).success,
    ).toBe(false)
  })
})