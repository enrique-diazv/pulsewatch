export interface AuthCredentials {
  email: string
  password: string
}

export interface AccessTokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface User {
  id: string
  email: string
  is_verified: boolean
  created_at: string
  updated_at: string
}