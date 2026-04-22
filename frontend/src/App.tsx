const summaryCards = [
  { label: "Cloud accounts", value: "3", trend: "+1 this week" },
  { label: "Open findings", value: "24", trend: "6 critical" },
  { label: "Risk score", value: "78", trend: "High attention" },
  { label: "Last scan", value: "12m", trend: "AWS production" },
];

const findings = [
  { service: "S3", title: "Public bucket access", severity: "Critical", status: "Open" },
  { service: "EC2", title: "Security group allows 0.0.0.0/0", severity: "High", status: "Open" },
  { service: "IAM", title: "User missing MFA", severity: "Medium", status: "Triaged" },
];

export function App() {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">CSPM</p>
          <h1>SentinelOps</h1>
        </div>
        <nav aria-label="Primary navigation">
          <a href="#overview">Overview</a>
          <a href="#accounts">Accounts</a>
          <a href="#findings">Findings</a>
          <a href="#scans">Scans</a>
        </nav>
      </aside>

      <section className="content" id="overview">
        <header className="topbar">
          <div>
            <p className="eyebrow">Cloud security dashboard</p>
            <h2>Security posture overview</h2>
          </div>
          <button type="button">Run scan</button>
        </header>

        <section className="summary-grid" aria-label="Security summary">
          {summaryCards.map((card) => (
            <article className="metric" key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
              <small>{card.trend}</small>
            </article>
          ))}
        </section>

        <section className="dashboard-grid">
          <article className="panel" id="findings">
            <div className="panel-heading">
              <h3>Priority findings</h3>
              <span>Live sample</span>
            </div>
            <div className="finding-list">
              {findings.map((finding) => (
                <div className="finding-row" key={finding.title}>
                  <div>
                    <strong>{finding.title}</strong>
                    <span>{finding.service}</span>
                  </div>
                  <span className={`severity ${finding.severity.toLowerCase()}`}>
                    {finding.severity}
                  </span>
                  <span>{finding.status}</span>
                </div>
              ))}
            </div>
          </article>

          <article className="panel" id="scans">
            <div className="panel-heading">
              <h3>Scan status</h3>
              <span>Healthy</span>
            </div>
            <div className="scan-card">
              <strong>Next milestone</strong>
              <p>Connect account onboarding, database persistence, scanners, and API data.</p>
            </div>
          </article>
        </section>
      </section>
    </main>
  );
}
