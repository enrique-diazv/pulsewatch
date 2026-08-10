import {
    Link,
    useParams,
} from 'react-router-dom'

import { useIncident } from '../features/incidents/queries.ts'
import { useMonitor } from '../features/monitors/queries.ts'

function formatTimestamp(value: string | null) {
    if (value === null) {
        return 'Ongoing'
    }

    return new Intl.DateTimeFormat(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
    }).format(new Date(value))
}

function formatDuration(
    startedAt: string,
    resolvedAt: string | null,
) {
    const start = new Date(startedAt).getTime()
    const end = resolvedAt
        ? new Date(resolvedAt).getTime()
        : Date.now()
    const totalMinutes = Math.max(
        0,
        Math.round((end - start) / 60_000),
    )

    if (totalMinutes < 60) {
        return `${totalMinutes} min`
    }

    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60

    return minutes === 0
        ? `${hours} hr`
        : `${hours} hr ${minutes} min`
}

export function IncidentDetailsPage() {
    const { incidentId = '' } = useParams()
    const incidentQuery = useIncident(incidentId)
    const monitorQuery = useMonitor(
        incidentQuery.data?.monitor_id ?? '',
    )

    if (incidentQuery.isPending) {
        return <p aria-live="polite">Loading incident...</p>
    }

    if (incidentQuery.isError) {
        return (
            <section className="error-state" role="alert">
                <h1>Unable to load incident</h1>
                <p>
                    The incident may not exist or may not belong
                    to you.
                </p>
                <Link
                    className="button button--secondary"
                    to="/incidents"
                >
                    Back to incidents
                </Link>
            </section>
        )
    }

    const incident = incidentQuery.data
    const monitor = monitorQuery.data

    return (
        <section aria-labelledby="incident-title">
            <Link className="back-link" to="/incidents">
                &larr; Back to incidents
            </Link>

            <header className="monitor-details__header">
                <div>
                    <p className="page-eyebrow">
                        Incident details
                    </p>
                    <div className="monitor-details__title">
                        <h1 id="incident-title">
                            {monitor?.name ?? 'Monitor incident'}
                        </h1>
                        <span
                            className={
                                incident.status === 'OPEN'
                                    ? 'incident-status incident-status--open'
                                    : 'incident-status incident-status--resolved'
                            }
                        >
                            {incident.status === 'OPEN'
                                ? 'Open'
                                : 'Resolved'}
                        </span>
                    </div>
                    <p className="page-description">
                        {incident.failure_reason}
                    </p>
                </div>

                {monitor ? (
                    <Link
                        className="button button--secondary"
                        to={`/monitors/${monitor.id}`}
                    >
                        View monitor
                    </Link>
                ) : null}
            </header>

            <dl className="details-grid">
                <div>
                    <dt>Started</dt>
                    <dd>
                        {formatTimestamp(incident.started_at)}
                    </dd>
                </div>
                <div>
                    <dt>Resolved</dt>
                    <dd>
                        {formatTimestamp(incident.resolved_at)}
                    </dd>
                </div>
                <div>
                    <dt>Duration</dt>
                    <dd>
                        {formatDuration(
                            incident.started_at,
                            incident.resolved_at,
                        )}
                    </dd>
                </div>
                <div>
                    <dt>Status</dt>
                    <dd>{incident.status}</dd>
                </div>
                <div>
                    <dt>Initial failed check</dt>
                    <dd>#{incident.initial_check_id}</dd>
                </div>
                <div>
                    <dt>Recovery check</dt>
                    <dd>
                        {incident.recovery_check_id === null
                            ? 'Pending'
                            : `#${incident.recovery_check_id}`}
                    </dd>
                </div>
            </dl>

            <section className="dashboard-section">
                <header className="section-header">
                    <div>
                        <h2>Failure reason</h2>
                        <p>
                            Condition that opened this incident.
                        </p>
                    </div>
                </header>
                <p className="incident-reason">
                    {incident.failure_reason}
                </p>
            </section>
        </section>
    )
}