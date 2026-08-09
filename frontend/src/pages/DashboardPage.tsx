import { Link } from 'react-router-dom'

import { MonitorStatusBadge } from '../components/common/MonitorStatusBadge.tsx'
import { useIncidents } from '../features/incidents/queries.ts'
import { useMonitors } from '../features/monitors/queries.ts'

export function DashboardPage() {
  const monitorsQuery = useMonitors()
  const incidentsQuery = useIncidents('OPEN')

  if (monitorsQuery.isPending || incidentsQuery.isPending) {
    return <p aria-live="polite">Loading dashboard…</p>
  }

  if (monitorsQuery.isError || incidentsQuery.isError) {
    return (
      <section className="error-state" role="alert">
        <h1>Unable to load dashboard</h1>
        <p>Check the API connection and try again.</p>
      </section>
    )
  }

  const monitors = monitorsQuery.data
  const openIncidents = incidentsQuery.data
  const operationalCount = monitors.filter(
    (monitor) => monitor.status === 'UP',
  ).length
  const downCount = monitors.filter(
    (monitor) => monitor.status === 'DOWN',
  ).length
  const degradedCount = monitors.filter(
    (monitor) => monitor.status === 'DEGRADED',
  ).length

  return (
    <section aria-labelledby="dashboard-title">
      <header className="page-header">
        <div>
          <p className="page-eyebrow">Monitoring overview</p>
          <h1 id="dashboard-title">Dashboard</h1>
          <p className="page-description">
            Monitor health and active incidents from one place.
          </p>
        </div>

        <Link
          className="button button--primary"
          to="/monitors/new"
        >
          Add monitor
        </Link>
      </header>

      <div className="metric-grid">
        <article className="metric-card">
          <p>Total monitors</p>
          <strong>{monitors.length}</strong>
          <span>Configured endpoints</span>
        </article>

        <article className="metric-card metric-card--success">
          <p>Operational</p>
          <strong>{operationalCount}</strong>
          <span>Passing checks</span>
        </article>

        <article className="metric-card metric-card--danger">
          <p>Down</p>
          <strong>{downCount}</strong>
          <span>Failure threshold reached</span>
        </article>

        <article className="metric-card metric-card--warning">
          <p>Degraded</p>
          <strong>{degradedCount}</strong>
          <span>Performance affected</span>
        </article>

        <article className="metric-card metric-card--danger">
          <p>Active incidents</p>
          <strong>{openIncidents.length}</strong>
          <span>Require attention</span>
        </article>
      </div>

      <section
        className="dashboard-section"
        aria-labelledby="monitor-snapshot-title"
      >
        <header className="section-header">
          <div>
            <h2 id="monitor-snapshot-title">Monitor snapshot</h2>
            <p>Current state of your most recent monitors.</p>
          </div>

          <Link to="/monitors">View all monitors</Link>
        </header>

        {monitors.length === 0 ? (
          <div className="empty-state">
            <h2>No monitors yet</h2>
            <p>Create a monitor to begin collecting health data.</p>
          </div>
        ) : (
          <div className="snapshot-list">
            {monitors.slice(0, 5).map((monitor) => (
              <Link
                className="snapshot-row"
                key={monitor.id}
                to={`/monitors/${monitor.id}`}
              >
                <div>
                  <strong>{monitor.name}</strong>
                  <span>{monitor.url}</span>
                </div>

                <MonitorStatusBadge status={monitor.status} />
              </Link>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}