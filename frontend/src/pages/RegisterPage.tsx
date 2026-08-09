import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'

import { registerSchema } from '../features/auth/schemas.ts'
import type { RegisterFormValues } from '../features/auth/schemas.ts'
import { useAuth } from '../features/auth/useAuth.ts'
import { ApiError } from '../services/api/client.ts'

function getRegistrationErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message
  }

  return 'Unable to create your account. Please try again.'
}

export function RegisterPage() {
  const { register: createAccount } = useAuth()
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    setError,
    formState: {
      errors,
      isSubmitting,
    },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
    },
  })

  async function submit(values: RegisterFormValues) {
    try {
      await createAccount({
        email: values.email,
        password: values.password,
      })
      navigate('/dashboard', { replace: true })
    } catch (error) {
      setError('root', {
        message: getRegistrationErrorMessage(error),
      })
    }
  }

  return (
    <section className="auth-content">
      <h1>Create your account</h1>
      <p>Start monitoring websites and APIs in minutes.</p>

      <form
        className="auth-form"
        noValidate
        onSubmit={handleSubmit(submit)}
      >
        {errors.root?.message ? (
          <div className="form-alert" role="alert">
            {errors.root.message}
          </div>
        ) : null}

        <div className="form-field">
          <label htmlFor="register-email">Email address</label>
          <input
            {...register('email')}
            aria-describedby={
              errors.email ? 'register-email-error' : undefined
            }
            aria-invalid={Boolean(errors.email)}
            autoComplete="email"
            id="register-email"
            inputMode="email"
            type="email"
          />
          {errors.email?.message ? (
            <p className="form-error" id="register-email-error">
              {errors.email.message}
            </p>
          ) : null}
        </div>

        <div className="form-field">
          <label htmlFor="register-password">Password</label>
          <input
            {...register('password')}
            aria-describedby={
              errors.password
                ? 'register-password-help register-password-error'
                : 'register-password-help'
            }
            aria-invalid={Boolean(errors.password)}
            autoComplete="new-password"
            id="register-password"
            type="password"
          />
          <p className="form-help" id="register-password-help">
            Use at least 6 characters.
          </p>
          {errors.password?.message ? (
            <p
              className="form-error"
              id="register-password-error"
            >
              {errors.password.message}
            </p>
          ) : null}
        </div>

        <div className="form-field">
          <label htmlFor="confirm-password">
            Confirm password
          </label>
          <input
            {...register('confirmPassword')}
            aria-describedby={
              errors.confirmPassword
                ? 'confirm-password-error'
                : undefined
            }
            aria-invalid={Boolean(errors.confirmPassword)}
            autoComplete="new-password"
            id="confirm-password"
            type="password"
          />
          {errors.confirmPassword?.message ? (
            <p
              className="form-error"
              id="confirm-password-error"
            >
              {errors.confirmPassword.message}
            </p>
          ) : null}
        </div>

        <button
          className="button button--primary auth-submit"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>

      <p className="auth-switch">
        Already have an account?{' '}
        <Link to="/login">Sign in</Link>
      </p>
    </section>
  )
}