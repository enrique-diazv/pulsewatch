import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { MonitorCheck } from '../../features/monitors/types.ts'

interface MonitorHistoryPanelProps {
  checks: MonitorCheck[]
}

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatChartTimestamp(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

export function MonitorHistoryPanel({
  checks,
}: MonitorHistoryPanelProps) {
  if (checks.length === 0) {
    return (
      <section className="history-panel">
        <header className="section-header">
          <div>
            <h2>Check history</h2>
            <p>Response times and recent availability.</p>
          </div>
        </header>

        <div className="history-empty">
          No checks have been recorded yet.
        </div>
      </section>
    )
  }

  const chartData = [...checks]
    .reverse()
    .map((check) => ({
      id: check.id,
      checkedAt: formatChartTimestamp(check.checked_at),
      responseTime: check.response_time_ms,
    }))

  return (
    <section className="history-panel">
      <header className="section-header">
        <div>
          <h2>Check history</h2>
          <p>Latest {checks.length} recorded checks.</p>
        </div>
      </header>

      <div
        aria-label="Monitor response time chart"
        className="history-chart"
        role="img"
      >
        <ResponsiveContainer height="100%" width="100%">
          <LineChart
            data={chartData}
            margin={{
              top: 12,
              right: 12,
              bottom: 4,
              left: 0,
            }}
          >
            <CartesianGrid
              stroke="#e4e7ec"
              strokeDasharray="3 5"
              vertical={false}
            />
            <XAxis
              axisLine={false}
              dataKey="checkedAt"
              minTickGap={24}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              unit=" ms"
              width={68}
            />
            <Tooltip />
            <Line
              activeDot={{ r: 5 }}
              dataKey="responseTime"
              dot={false}
              name="Response time"
              stroke="#2563eb"
              strokeWidth={2}
              type="monotone"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="history-table-wrapper">
        <table className="history-table">
          <thead>
            <tr>
              <th scope="col">Checked at</th>
              <th scope="col">Result</th>
              <th scope="col">Status</th>
              <th scope="col">Response</th>
              <th scope="col">Error</th>
            </tr>
          </thead>
          <tbody>
            {checks.slice(0, 10).map((check) => (
              <tr key={check.id}>
                <td>{formatTimestamp(check.checked_at)}</td>
                <td>
                  <span
                    className={
                      check.success
                        ? 'check-result check-result--success'
                        : 'check-result check-result--failure'
                    }
                  >
                    {check.success ? 'Success' : 'Failed'}
                  </span>
                </td>
                <td>{check.status_code ?? '—'}</td>
                <td>{check.response_time_ms} ms</td>
                <td>{check.error_type ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}