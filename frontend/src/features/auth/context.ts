import { createContext } from 'react'

import type { AuthCredentials, User } from './types.ts'

export type AuthStatus =
  | 'loading'
  | 'authenticated'
  | 'anonymous'

export interface AuthContextValue {
  user: User | null
  status: AuthStatus
  login: (credentials: AuthCredentials) => Promise<void>
  register: (credentials: AuthCredentials) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext =
  createContext<AuthContextValue | null>(null)