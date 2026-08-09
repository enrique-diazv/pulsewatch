import {
  apiRequest,
  clearAccessToken,
  setAccessToken,
} from '../../services/api/client.ts'
import type {
  AccessTokenResponse,
  AuthCredentials,
  User,
} from './types.ts'

let restoreSessionPromise: Promise<User> | null = null

export function registerUser(
  credentials: AuthCredentials,
) {
  return apiRequest<User>('/auth/register', {
    method: 'POST',
    json: credentials,
  })
}

export async function loginUser(
  credentials: AuthCredentials,
) {
  const token = await apiRequest<AccessTokenResponse>(
    '/auth/login',
    {
      method: 'POST',
      json: credentials,
    },
  )

  setAccessToken(token.access_token)

  return token
}

export async function refreshAccessToken() {
  const token = await apiRequest<AccessTokenResponse>(
    '/auth/refresh',
    {
      method: 'POST',
    },
  )

  setAccessToken(token.access_token)

  return token
}

export function getCurrentUser() {
  return apiRequest<User>('/auth/me', {
    authenticated: true,
  })
}

export function restoreUserSession() {
  if (restoreSessionPromise === null) {
    restoreSessionPromise = refreshAccessToken()
      .then(() => getCurrentUser())
      .finally(() => {
        restoreSessionPromise = null
      })
  }

  return restoreSessionPromise
}

export async function logoutUser() {
  try {
    await apiRequest<void>('/auth/logout', {
      method: 'POST',
    })
  } finally {
    clearAccessToken()
  }
}