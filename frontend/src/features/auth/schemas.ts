import { z } from 'zod'

const emailSchema = z
  .string()
  .trim()
  .email('Enter a valid email address')

export const loginSchema = z.object({
  email: emailSchema,
  password: z
    .string()
    .min(1, 'Enter your password')
    .max(128, 'Password is too long'),
})

export const registerSchema = z
  .object({
    email: emailSchema,
    password: z
      .string()
      .min(6, 'Password must contain at least 6 characters')
      .max(128, 'Password is too long'),
    confirmPassword: z.string(),
  })
  .refine(
    (values) => values.password === values.confirmPassword,
    {
      message: 'Passwords do not match',
      path: ['confirmPassword'],
    },
  )

export type LoginFormValues = z.infer<typeof loginSchema>
export type RegisterFormValues = z.infer<typeof registerSchema>