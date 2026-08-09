import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import {
  Link,
  useLocation,
  useNavigate,
} from 'react-router-dom'

import { loginSchema } from '../features/auth/schemas.ts'
import type { LoginFormValues } from '../features/auth/schemas.ts'
import { useAuth } from '../features/auth/useAuth.ts'
import { ApiError } from '../services/api/client.ts'

interface LoginLocationState {
  from?: {
    pathname?: string
  }
}

function getLoginErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message
  }

  return 'Unable to sign in. Please try again.'
}

export function LoginPage() {
  const { login } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    setError,
    formState: {
      errors,
      isSubmitting,
    },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  async function submit(values: LoginFormValues) {
    try {
      await login(values)

      const state = location.state as LoginLocationState | null
      const destination = state?.from?.pathname ?? '/dashboard'

      navigate(destination, { replace: true })
    } catch (error) {
      setError('root', {
        message: getLoginErrorMessage(error),
      })
    }
  }

  return (
    <section className="auth-content">
      <h1>Welcome back</h1>
      <p>Sign in to view your monitoring workspace.</p>

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
          <label htmlFor="email">Email address</label>
          <input
            {...register('email')}
            aria-describedby={
              errors.email ? 'email-error' : undefined
            }
            aria-invalid={Boolean(errors.email)}
            autoComplete="email"
            id="email"
            inputMode="email"
            type="email"
          />
          {errors.email?.message ? (
            <p className="form-error" id="email-error">
              {errors.email.message}
            </p>
          ) : null}
        </div>

        <div className="form-field">
          <label htmlFor="password">Password</label>
          <input
            {...register('password')}
            aria-describedby={
              errors.password ? 'password-error' : undefined
            }
            aria-invalid={Boolean(errors.password)}
            autoComplete="current-password"
            id="password"
            type="password"
          />
          {errors.password?.message ? (
            <p className="form-error" id="password-error">
              {errors.password.message}
            </p>
          ) : null}
        </div>

        <button
          className="button button--primary auth-submit"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <p className="auth-switch">
        New to PulseWatch?{' '}
        <Link to="/register">Create an account</Link>
      </p>
    </section>
  )
}