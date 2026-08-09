import { MonitorStatusBadge } from '../components/common/MonitorStatusBadge.tsx'
import { useMonitors } from '../features/monitors/queries.ts'
import { Link } from 'react-router-dom'
function formatLastCheck(value: string | null) {
    if (value === null) {
        return 'Not checked yet'
    }

    return new Intl.DateTimeFormat(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
    }).format(new Date(value))
}

export function MonitorsPage() {
    const {
        data: monitors,
        isPending,
        isError,
        refetch,
    } = useMonitors()

    if (isPending) {
        return (
            <section aria-live="polite">
                <p>Loading monitors…</p>
            </section>
        )
    }

    if (isError) {
        return (
            <section className="error-state" role="alert">
                <h1>Unable to load monitors</h1>
                <p>Check the API connection and try again.</p>
                <button
                    className="button"
                    onClick={() => void refetch()}
                    type="button"
                >
                    Try again
                </button>
            </section>
        )
    }

    return (
        <section aria-labelledby="monitors-title">
            <header className="page-header">
                <div>
                    <p className="page-eyebrow">Endpoint management</p>
                    <h1 id="monitors-title">Monitors</h1>
                    <p className="page-description">
                        Track the current state and recent activity of your
                        websites and APIs.
                    </p>
                </div>
                <Link
                    className="button button--primary"
                    to="/monitors/new"
                >
                    Add monitor
                </Link>
            </header>

            {monitors.length === 0 ? (
                <div className="empty-state">
                    <h2>No monitors yet</h2>
                    <p>Create your first monitor to start collecting data.</p>
                </div>
            ) : (
                <div className="monitor-grid">
                    {monitors.map((monitor) => (
                        <article className="monitor-card" key={monitor.id}>
                            <div className="monitor-card__header">
                                <div>
                                    <p className="monitor-card__method">
                                        {monitor.method}
                                    </p>
                                    <h2>
                                        <Link
                                            className="monitor-card__link"
                                            to={`/monitors/${monitor.id}`}
                                        >
                                            {monitor.name}
                                        </Link>
                                    </h2>
                                </div>

                                <MonitorStatusBadge status={monitor.status} />
                            </div>

                            <p className="monitor-card__url" title={monitor.url}>
                                {monitor.url}
                            </p>

                            <dl className="monitor-card__metrics">
                                <div>
                                    <dt>Interval</dt>
                                    <dd>{monitor.interval_seconds}s</dd>
                                </div>
                                <div>
                                    <dt>Last check</dt>
                                    <dd>{formatLastCheck(monitor.last_checked_at)}</dd>
                                </div>
                            </dl>
                        </article>
                    ))}
                </div>
            )}
        </section>
    )
}