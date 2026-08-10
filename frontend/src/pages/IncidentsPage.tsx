import {
  Link,
  useSearchParams,
} from 'react-router-dom'

import { useIncidents } from '../features/incidents/queries.ts'
import type { IncidentStatus } from '../features/incidents/types.ts'
import { useMonitors } from '../features/monitors/queries.ts'

function parseStatus(value: string | null) {
  if (value === 'OPEN' || value === 'RESOLVED') {
    return value
  }

  return undefined
}

function formatTimestamp(value: string | null) {
  if (value === null) {
    return 'Ongoing'
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

interface FilterButtonProps {
  active: boolean
  label: string
  onClick: () => void
}

function FilterButton({
  active,
  label,
  onClick,
}: FilterButtonProps) {
  return (
    <button
      aria-pressed={active}
      className={
        active
          ? 'filter-button filter-button--active'
          : 'filter-button'
      }
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  )
}

export function IncidentsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedStatus = parseStatus(searchParams.get('status'))
  const incidentsQuery = useIncidents(selectedStatus)
  const monitorsQuery = useMonitors()

  function selectStatus(status?: IncidentStatus) {
    if (status === undefined) {
      setSearchParams({})
      return
    }

    setSearchParams({ status })
  }

  if (incidentsQuery.isPending) {
    return <p aria-live="polite">Loading incidents…</p>
  }

  if (incidentsQuery.isError) {
    return (
      <section className="error-state" role="alert">
        <h1>Unable to load incidents</h1>
        <p>Check the API connection and try again.</p>
      </section>
    )
  }

  const incidents = incidentsQuery.data
  const monitors = monitorsQuery.data ?? []

  return (
    <section aria-labelledby="incidents-title">
      <header className="page-header">
        <div>
          <p className="page-eyebrow">Operational history</p>
          <h1 id="incidents-title">Incidents</h1>
          <p className="page-description">
            Review outages and recoveries detected by PulseWatch.
          </p>
        </div>
      </header>

      <div
        className="filter-group"
        aria-label="Filter incidents"
      >
        <FilterButton
          active={selectedStatus === undefined}
          label="All"
          onClick={() => selectStatus()}
        />
        <FilterButton
          active={selectedStatus === 'OPEN'}
          label="Open"
          onClick={() => selectStatus('OPEN')}
        />
        <FilterButton
          active={selectedStatus === 'RESOLVED'}
          label="Resolved"
          onClick={() => selectStatus('RESOLVED')}
        />
      </div>

      {incidents.length === 0 ? (
        <div className="empty-state">
          <h2>No incidents found</h2>
          <p>
            Incidents will appear after a monitor reaches its
            failure threshold.
          </p>
        </div>
      ) : (
        <div className="incident-list">
          {incidents.map((incident) => {
            const monitor = monitors.find(
              (item) => item.id === incident.monitor_id,
            )

            return (
              <Link
                className="incident-card incident-card--link"
                key={incident.id}
                to={`/incidents/${incident.id}`}
              >
                <div className="incident-card__content">
                  <div className="incident-card__heading">
                    <span
                      className={
                        incident.status === 'OPEN'
                          ? 'incident-status incident-status--open'
                          : 'incident-status incident-status--resolved'
                      }
                    >
                      {incident.status === 'OPEN'
                        ? 'Open incident'
                        : 'Resolved'}
                    </span>
                    <h2>{monitor?.name ?? 'Unknown monitor'}</h2>
                  </div>

                  <p>{incident.failure_reason}</p>
                </div>

                <dl className="incident-card__timeline">
                  <div>
                    <dt>Started</dt>
                    <dd>{formatTimestamp(incident.started_at)}</dd>
                  </div>
                  <div>
                    <dt>Resolved</dt>
                    <dd>{formatTimestamp(incident.resolved_at)}</dd>
                  </div>
                </dl>
              </Link>
            )
          })}
        </div>
      )}
    </section>
  )
}