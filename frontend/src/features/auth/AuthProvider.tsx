import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { PropsWithChildren } from 'react'

import { clearAccessToken } from '../../services/api/client.ts'
import {
  getCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  restoreUserSession,
} from './api.ts'
import {
  AuthContext,
  type AuthStatus,
} from './context.ts'
import type { AuthCredentials, User } from './types.ts'

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  useEffect(() => {
    let active = true

    async function restoreSession() {
      try {
        const restoredUser = await restoreUserSession()

        if (active) {
          setUser(restoredUser)
          setStatus('authenticated')
        }
      } catch {
        clearAccessToken()

        if (active) {
          setUser(null)
          setStatus('anonymous')
        }
      }
    }

    void restoreSession()

    return () => {
      active = false
    }
  }, [])

  const login = useCallback(
    async (credentials: AuthCredentials) => {
      await loginUser(credentials)
      const authenticatedUser = await getCurrentUser()

      setUser(authenticatedUser)
      setStatus('authenticated')
    },
    [],
  )

  const register = useCallback(
    async (credentials: AuthCredentials) => {
      await registerUser(credentials)
      await loginUser(credentials)
      const authenticatedUser = await getCurrentUser()

      setUser(authenticatedUser)
      setStatus('authenticated')
    },
    [],
  )

  const logout = useCallback(async () => {
    try {
      await logoutUser()
    } finally {
      setUser(null)
      setStatus('anonymous')
    }
  }, [])

  const value = useMemo(
    () => ({
      user,
      status,
      login,
      register,
      logout,
    }),
    [user, status, login, register, logout],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}