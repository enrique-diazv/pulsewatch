import type {
    MetricsRange,
    MonitorMetrics,
} from '../../features/monitors/types.ts'

interface MonitorMetricsPanelProps {
    metrics: MonitorMetrics | undefined
    metricsRange: MetricsRange
    pending: boolean
    onRangeChange: (metricsRange: MetricsRange) => void
}

const METRICS_RANGES: ReadonlyArray<{
    label: string
    value: MetricsRange
}> = [
        {
            label: '24 hours',
            value: '24h',
        },
        {
            label: '7 days',
            value: '7d',
        },
        {
            label: '30 days',
            value: '30d',
        },
    ]

function formatUptime(value: number | null | undefined) {
    return value === null || value === undefined
        ? 'Not available'
        : `${value.toFixed(2)}%`
}

function formatResponseTime(
    value: number | null | undefined,
) {
    return value === null || value === undefined
        ? 'Not available'
        : `${Math.round(value)} ms`
}

export function MonitorMetricsPanel({
    metrics,
    metricsRange,
    pending,
    onRangeChange,
}: MonitorMetricsPanelProps) {
    return (
        <section
            aria-labelledby="monitor-metrics-title"
            className="dashboard-section"
        >
            <header className="section-header">
                <div>
                    <h2 id="monitor-metrics-title">
                        Performance summary
                    </h2>
                    <p>
                        Availability and response metrics for the
                        selected range.
                    </p>
                </div>

                <div
                    aria-label="Metrics range"
                    className="filter-group metrics-range"
                    role="group"
                >
                    {METRICS_RANGES.map((rangeOption) => (
                        <button
                            aria-pressed={
                                metricsRange === rangeOption.value
                            }
                            className={
                                metricsRange === rangeOption.value
                                    ? 'filter-button filter-button--active'
                                    : 'filter-button'
                            }
                            key={rangeOption.value}
                            onClick={() =>
                                onRangeChange(rangeOption.value)
                            }
                            type="button"
                        >
                            {rangeOption.label}
                        </button>
                    ))}
                </div>
            </header>

            <div
                aria-busy={pending}
                className="metric-grid metrics-summary-grid"
            >
                <article className="metric-card metric-card--success">
                    <p>Uptime</p>
                    <strong>
                        {pending
                            ? 'Loading...'
                            : formatUptime(
                                metrics?.uptime_percentage,
                            )}
                    </strong>
                    <span>Successful checks in this range</span>
                </article>

                <article className="metric-card">
                    <p>Average response</p>
                    <strong>
                        {pending
                            ? 'Loading...'
                            : formatResponseTime(
                                metrics?.average_response_time_ms,
                            )}
                    </strong>
                    <span>Mean HTTP response duration</span>
                </article>

                <article className="metric-card">
                    <p>Total checks</p>
                    <strong>
                        {pending
                            ? 'Loading...'
                            : (metrics?.total_checks ?? 0)}
                    </strong>
                    <span>Completed monitoring attempts</span>
                </article>

                <article className="metric-card metric-card--danger">
                    <p>Failed checks</p>
                    <strong>
                        {pending
                            ? 'Loading...'
                            : (metrics?.failed_checks ?? 0)}
                    </strong>
                    <span>Checks that did not meet expectations</span>
                </article>
            </div>
        </section>
    )
}