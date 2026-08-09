import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../../features/auth/useAuth.ts'
import { SessionLoader } from '../common/SessionLoader.tsx'

export function PublicOnlyRoute() {
  const { status } = useAuth()

  if (status === 'loading') {
    return <SessionLoader />
  }

  if (status === 'authenticated') {
    return <Navigate replace to="/dashboard" />
  }

  return <Outlet />
}