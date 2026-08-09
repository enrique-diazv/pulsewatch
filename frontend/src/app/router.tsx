import {
  Navigate,
  createBrowserRouter,
} from 'react-router-dom'

import { IncidentsPage } from '../pages/IncidentsPage.tsx'
import { CreateMonitorPage } from '../pages/CreateMonitorPage.tsx'
import { ProtectedRoute } from '../components/auth/ProtectedRoute.tsx'
import { PublicOnlyRoute } from '../components/auth/PublicOnlyRoute.tsx'
import { AppLayout } from '../components/layout/AppLayout.tsx'
import { AuthLayout } from '../components/layout/AuthLayout.tsx'
import { DashboardPage } from '../pages/DashboardPage.tsx'
import { LoginPage } from '../pages/LoginPage.tsx'
import { NotFoundPage } from '../pages/NotFoundPage.tsx'
import { RegisterPage } from '../pages/RegisterPage.tsx'
import { MonitorsPage } from '../pages/MonitorsPage.tsx'
import { MonitorDetailsPage } from '../pages/MonitorDetailsPage.tsx'
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate replace to="/dashboard" />,
  },
  {
    element: <PublicOnlyRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          {
            path: '/login',
            element: <LoginPage />,
          },
          {
            path: '/register',
            element: <RegisterPage />,
          },
        ],
      },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            path: '/dashboard',
            element: <DashboardPage />,
          },
          {
            path: '/monitors',
            element: <MonitorsPage />,
          },
          {
            path: '/monitors/new',
            element: <CreateMonitorPage />,
          },
          {
            path: '/monitors/:monitorId/edit',
            element: <CreateMonitorPage mode="edit" />,
          },
          {
            path: '/monitors/:monitorId',
            element: <MonitorDetailsPage />,
          },
          {
            path: '/incidents',
            element: <IncidentsPage />,
          },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])