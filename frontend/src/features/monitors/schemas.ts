import { z } from 'zod'

export const monitorCreateSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Enter a monitor name')
    .max(120, 'Name is too long'),
  url: z
    .string()
    .trim()
    .url('Enter a valid URL')
    .refine(
      (value) => {
        const protocol = new URL(value).protocol

        return protocol === 'http:' || protocol === 'https:'
      },
      'Only HTTP and HTTPS URLs are allowed',
    ),
  interval_seconds: z
    .number()
    .int()
    .min(30, 'Minimum interval is 30 seconds')
    .max(86400, 'Maximum interval is 24 hours'),
  timeout_seconds: z
    .number()
    .int()
    .min(1, 'Minimum timeout is 1 second')
    .max(60, 'Maximum timeout is 60 seconds'),
  expected_status: z
    .number()
    .int()
    .min(100, 'Enter a valid HTTP status')
    .max(599, 'Enter a valid HTTP status'),
  failure_threshold: z
    .number()
    .int()
    .min(1)
    .max(10),
  recovery_threshold: z
    .number()
    .int()
    .min(1)
    .max(10),
})

export type MonitorCreateFormValues =
  z.infer<typeof monitorCreateSchema>