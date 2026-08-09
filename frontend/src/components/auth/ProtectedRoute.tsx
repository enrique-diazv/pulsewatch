import {
  Navigate,
  Outlet,
  useLocation,
} from 'react-router-dom'

import { useAuth } from '../../features/auth/useAuth.ts'
import { SessionLoader } from '../common/SessionLoader.tsx'

export function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') {
    return <SessionLoader />
  }

  if (status === 'anonymous') {
    return (
      <Navigate
        replace
        state={{ from: location }}
        to="/login"
      />
    )
  }

  return <Outlet />
}