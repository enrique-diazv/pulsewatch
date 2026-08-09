export function MonitoringBackdrop() {
  return (
    <div aria-hidden="true" className="monitoring-visual">
      <svg
        className="monitoring-line"
        preserveAspectRatio="none"
        viewBox="0 0 600 220"
      >
        <defs>
          <clipPath id="monitoring-chart-reveal">
            <rect
              className="monitoring-line__reveal"
              height="220"
              width="600"
              x="0"
              y="0"
            />
          </clipPath>
        </defs>

        <g className="monitoring-line__grid">
          <line x1="0" x2="600" y1="40" y2="40" />
          <line x1="0" x2="600" y1="80" y2="80" />
          <line x1="0" x2="600" y1="120" y2="120" />
          <line x1="0" x2="600" y1="160" y2="160" />
          <line x1="0" x2="600" y1="200" y2="200" />
        </g>

        <g
          className="monitoring-line__series"
          clipPath="url(#monitoring-chart-reveal)"
        >
          <path
            className="monitoring-line__path"
            d="
              M0 168
              L90 112
              L180 146
              L275 72
              L365 30
              L470 88
              L600 136
            "
          />

          <g className="monitoring-line__points">
            <circle cx="0" cy="168" r="4" />
            <circle cx="90" cy="112" r="4" />
            <circle cx="180" cy="146" r="4" />
            <circle cx="275" cy="72" r="4" />
            <circle cx="365" cy="30" r="4" />
            <circle cx="470" cy="88" r="4" />
            <circle cx="600" cy="136" r="4" />
          </g>
        </g>
      </svg>

      <div className="monitoring-bars">
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
      </div>
    </div>
  )
}