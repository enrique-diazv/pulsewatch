import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../../features/auth/useAuth.ts'

function navigationClassName({
  isActive,
}: {
  isActive: boolean
}) {
  return isActive
    ? 'nav-link nav-link--active'
    : 'nav-link'
}

export function AppLayout() {
  const { user, logout } = useAuth()

  function handleLogout() {
    void logout().catch(() => undefined)
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <NavLink className="app-brand" to="/dashboard">
          <span aria-hidden="true" className="app-brand__mark">
            P
          </span>
          <span>PulseWatch</span>
        </NavLink>

        <div className="app-navigation">
          <p className="app-navigation__label">Workspace</p>

          <nav aria-label="Primary navigation">
            <NavLink
              className={navigationClassName}
              to="/dashboard"
            >
              Overview
            </NavLink>
            <NavLink
              className={navigationClassName}
              to="/monitors"
            >
              Monitors
            </NavLink>
            <NavLink
              className={navigationClassName}
              to="/incidents"
            >
              Incidents
            </NavLink>
          </nav>
        </div>

        <div className="sidebar-account">
          <div>
            <span>Signed in as</span>
            <strong title={user?.email}>{user?.email}</strong>
          </div>

          <button
            className="sidebar-logout"
            onClick={handleLogout}
            type="button"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="app-content">
        <Outlet />
      </main>
    </div>
  )
}