import { Link, Outlet } from 'react-router-dom'

import { MonitoringBackdrop } from '../auth/MonitoringBackdrop.tsx'

export function AuthLayout() {
  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <Link className="app-brand auth-brand" to="/login">
          <span aria-hidden="true" className="app-brand__mark">
            P
          </span>
          <span>PulseWatch</span>
        </Link>

        <Outlet />
      </section>

      <aside className="auth-aside">
        <MonitoringBackdrop />

        <div className="auth-aside__content">
          <p className="page-eyebrow">Reliable monitoring</p>
          <h2>Know when your services need attention.</h2>
          <p>
            Track availability, response times, and incidents
            from a single operational workspace.
          </p>
        </div>
      </aside>
    </main>
  )
}