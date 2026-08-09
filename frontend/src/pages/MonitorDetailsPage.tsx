import { lazy, Suspense, useState } from 'react'
import {
    Link,
    useParams,
} from 'react-router-dom'

import { MonitorStatusBadge } from '../components/common/MonitorStatusBadge.tsx'
import {
  useMonitor,
  useMonitorChecks,
  usePauseMonitor,
  useQueueMonitorCheck,
  useResumeMonitor,
} from '../features/monitors/queries.ts'
import { ApiError } from '../services/api/client.ts'
interface Feedback {
    type: 'success' | 'error'
    message: string
}
const MonitorHistoryPanel = lazy(async () => {
    const module = await import(
        '../components/monitors/MonitorHistoryPanel.tsx'
    )

    return {
        default: module.MonitorHistoryPanel,
    }
})

function formatTimestamp(value: string | null) {
    if (value === null) {
        return 'Not available'
    }

    return new Intl.DateTimeFormat(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
    }).format(new Date(value))
}

function getActionError(error: unknown) {
    if (error instanceof ApiError) {
        return error.message
    }

    return 'The action could not be completed.'
}

export function MonitorDetailsPage() {
    const { monitorId = '' } = useParams()
    const [feedback, setFeedback] = useState<Feedback | null>(null)
    const monitorQuery = useMonitor(monitorId)
    const checkHistoryQuery = useMonitorChecks(monitorId)
    const pauseMonitor = usePauseMonitor()
    const resumeMonitor = useResumeMonitor()
    const queueCheck = useQueueMonitorCheck()

    if (monitorQuery.isPending) {
        return <p aria-live="polite">Loading monitor...</p>
    }

    if (monitorQuery.isError) {
        return (
            <section className="error-state" role="alert">
                <h1>Unable to load monitor</h1>
                <p>The monitor may not exist or may not belong to you.</p>
                <Link className="button button--secondary" to="/monitors">
                    Back to monitors
                </Link>
            </section>
        )
    }

    const monitor = monitorQuery.data
    const stateActionPending =
        pauseMonitor.isPending || resumeMonitor.isPending

    async function toggleMonitorState() {
        setFeedback(null)

        try {
            if (monitor.is_active) {
                await pauseMonitor.mutateAsync(monitor.id)
                setFeedback({
                    type: 'success',
                    message: 'Monitor paused.',
                })
            } else {
                await resumeMonitor.mutateAsync(monitor.id)
                setFeedback({
                    type: 'success',
                    message: 'Monitor resumed and scheduled.',
                })
            }
        } catch (error) {
            setFeedback({
                type: 'error',
                message: getActionError(error),
            })
        }
    }

    async function runManualCheck() {
        setFeedback(null)

        try {
            await queueCheck.mutateAsync(monitor.id)
            setFeedback({
                type: 'success',
                message: 'Monitor check queued successfully.',
            })
        } catch (error) {
            setFeedback({
                type: 'error',
                message: getActionError(error),
            })
        }
    }

    return (
        <section aria-labelledby="monitor-title">
            <Link className="back-link" to="/monitors">
                &larr; Back to monitors
            </Link>

            <header className="monitor-details__header">
                <div>
                    <p className="page-eyebrow">{monitor.method} monitor</p>
                    <div className="monitor-details__title">
                        <h1 id="monitor-title">{monitor.name}</h1>
                        <MonitorStatusBadge status={monitor.status} />
                    </div>
                    <p className="page-description">{monitor.url}</p>
                </div>

                <div className="monitor-actions">
                    <Link
                        className="button button--secondary"
                        to={`/monitors/${monitor.id}/edit`}
                    >
                        Edit
                    </Link>
                    <button
                        className="button button--secondary"
                        disabled={stateActionPending}
                        onClick={() => void toggleMonitorState()}
                        type="button"
                    >
                        {monitor.is_active ? 'Pause' : 'Resume'}
                    </button>
                    <button
                        className="button button--primary"
                        disabled={queueCheck.isPending || !monitor.is_active}
                        onClick={() => void runManualCheck()}
                        type="button"
                    >
                        {queueCheck.isPending ? 'Queueing...' : 'Run check'}
                    </button>
                </div>
            </header>

            {feedback ? (
                <div
                    className={
                        feedback.type === 'error'
                            ? 'feedback feedback--error'
                            : 'feedback feedback--success'
                    }
                    role={feedback.type === 'error' ? 'alert' : 'status'}
                >
                    {feedback.message}
                </div>
            ) : null}

            <dl className="details-grid">
                <div>
                    <dt>Expected status</dt>
                    <dd>{monitor.expected_status}</dd>
                </div>
                <div>
                    <dt>Interval</dt>
                    <dd>{monitor.interval_seconds} seconds</dd>
                </div>
                <div>
                    <dt>Timeout</dt>
                    <dd>{monitor.timeout_seconds} seconds</dd>
                </div>
                <div>
                    <dt>Failure threshold</dt>
                    <dd>{monitor.failure_threshold}</dd>
                </div>
                <div>
                    <dt>Recovery threshold</dt>
                    <dd>{monitor.recovery_threshold}</dd>
                </div>
                <div>
                    <dt>Last check</dt>
                    <dd>{formatTimestamp(monitor.last_checked_at)}</dd>
                </div>
                <div>
                    <dt>Next check</dt>
                    <dd>{formatTimestamp(monitor.next_check_at)}</dd>
                </div>
                <div>
                    <dt>Monitoring</dt>
                    <dd>{monitor.is_active ? 'Active' : 'Paused'}</dd>
                </div>
            </dl>
            {checkHistoryQuery.isPending ? (
                <section className="history-panel">
                    <p aria-live="polite">Loading check history...</p>
                </section>
            ) : null}

            {checkHistoryQuery.isError ? (
                <section className="history-panel" role="alert">
                    <h2>Unable to load check history</h2>
                    <p>The latest checks could not be retrieved.</p>
                </section>
            ) : null}

            {checkHistoryQuery.data ? (
                <Suspense
                    fallback={
                        <section className="history-panel">
                            <p aria-live="polite">Loading chart...</p>
                        </section>
                    }
                >
                    <MonitorHistoryPanel checks={checkHistoryQuery.data} />
                </Suspense>
            ) : null}
        </section>
    )
}