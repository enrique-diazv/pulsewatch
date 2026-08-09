export function SessionLoader() {
  return (
    <main className="session-loader" aria-live="polite">
      <span aria-hidden="true" className="session-loader__indicator" />
      <p>Restoring your session…</p>
    </main>
  )
}