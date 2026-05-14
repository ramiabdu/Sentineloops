type MetricCard = {
  label: string;
  value: string;
  detail: string;
  tone: "steady" | "warning" | "danger" | "calm";
};

type AccountRow = {
  name: string;
  provider: string;
  status: "Active" | "Scanning" | "Needs review";
  findings: number;
  risk: number;
};

type FindingRow = {
  resource: string;
  account: string;
  severity: "Critical" | "High" | "Medium";
  scanner: string;
  lastSeen: string;
};

type ScanRow = {
  account: string;
  status: "Completed" | "Running" | "Queued";
  duration: string;
  findings: number;
};

const metrics: MetricCard[] = [
  { label: "Cloud accounts", value: "3", detail: "2 active, 1 scanning", tone: "steady" },
  { label: "Open findings", value: "24", detail: "8 need review today", tone: "warning" },
  { label: "Critical risk", value: "6", detail: "4 internet exposed", tone: "danger" },
  { label: "Scan coverage", value: "92%", detail: "Last run 12 minutes ago", tone: "calm" },
];

const accountRows: AccountRow[] = [
  { name: "AWS production", provider: "AWS", status: "Scanning", findings: 14, risk: 84 },
  { name: "AWS staging", provider: "AWS", status: "Active", findings: 7, risk: 58 },
  { name: "AWS sandbox", provider: "AWS", status: "Needs review", findings: 3, risk: 41 },
];

const findings: FindingRow[] = [
  {
    resource: "sg-09f3 allows public SSH",
    account: "AWS production",
    severity: "Critical",
    scanner: "Security group exposure",
    lastSeen: "4m ago",
  },
  {
    resource: "public-assets bucket ACL",
    account: "AWS production",
    severity: "High",
    scanner: "S3 public bucket",
    lastSeen: "12m ago",
  },
  {
    resource: "alice console MFA missing",
    account: "AWS staging",
    severity: "Medium",
    scanner: "IAM without MFA",
    lastSeen: "18m ago",
  },
];

const scans: ScanRow[] = [
  { account: "AWS production", status: "Running", duration: "01:44", findings: 6 },
  { account: "AWS staging", status: "Completed", duration: "03:18", findings: 7 },
  { account: "AWS sandbox", status: "Queued", duration: "Pending", findings: 0 },
];

const severityBreakdown = [
  { label: "Critical", value: 6, max: 24, className: "critical" },
  { label: "High", value: 8, max: 24, className: "high" },
  { label: "Medium", value: 7, max: 24, className: "medium" },
  { label: "Low", value: 3, max: 24, className: "low" },
];

export function App() {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">
            S
          </span>
          <div>
            <p className="eyebrow">CSPM</p>
            <h1>SentinelOps</h1>
          </div>
        </div>

        <nav className="main-nav" aria-label="Primary navigation">
          <a className="active" href="#overview">
            Overview
          </a>
          <a href="#accounts">Accounts</a>
          <a href="#findings">Findings</a>
          <a href="#scans">Scans</a>
        </nav>
      </aside>

      <section className="workspace" id="overview">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Cloud security dashboard</p>
            <h2>Security posture overview</h2>
          </div>
          <div className="header-actions" aria-label="Dashboard controls">
            <div className="segmented-control" aria-label="Time range">
              <button className="selected" type="button">
                24h
              </button>
              <button type="button">7d</button>
              <button type="button">30d</button>
            </div>
            <button className="primary-action" type="button">
              Run scan
            </button>
          </div>
        </header>

        <section className="metric-grid" aria-label="Security summary">
          {metrics.map((metric) => (
            <article className={`metric-card ${metric.tone}`} key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.detail}</small>
            </article>
          ))}
        </section>

        <section className="dashboard-grid">
          <section className="panel wide-panel" id="findings" aria-labelledby="findings-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Priority queue</p>
                <h3 id="findings-title">Findings requiring action</h3>
              </div>
              <a href="#findings">View all</a>
            </div>

            <div className="finding-table" role="table" aria-label="Priority findings">
              <div className="table-head" role="row">
                <span role="columnheader">Resource</span>
                <span role="columnheader">Account</span>
                <span role="columnheader">Severity</span>
                <span role="columnheader">Last seen</span>
              </div>
              {findings.map((finding) => (
                <div className="table-row" role="row" key={finding.resource}>
                  <div role="cell">
                    <strong>{finding.resource}</strong>
                    <small>{finding.scanner}</small>
                  </div>
                  <span role="cell">{finding.account}</span>
                  <span
                    className={`severity-pill ${finding.severity.toLowerCase()}`}
                    role="cell"
                  >
                    {finding.severity}
                  </span>
                  <span role="cell">{finding.lastSeen}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="panel" aria-labelledby="severity-title">
            <div className="panel-heading compact">
              <div>
                <p className="eyebrow">Risk mix</p>
                <h3 id="severity-title">Severity breakdown</h3>
              </div>
            </div>
            <div className="severity-bars" aria-label="Findings by severity">
              {severityBreakdown.map((severity) => (
                <div className="bar-row" key={severity.label}>
                  <div className="bar-label">
                    <span>{severity.label}</span>
                    <strong>{severity.value}</strong>
                  </div>
                  <div className="bar-track">
                    <span
                      className={`bar-fill ${severity.className}`}
                      style={{ width: `${(severity.value / severity.max) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel" id="accounts" aria-labelledby="accounts-title">
            <div className="panel-heading compact">
              <div>
                <p className="eyebrow">Inventory</p>
                <h3 id="accounts-title">Cloud accounts</h3>
              </div>
            </div>
            <div className="account-list">
              {accountRows.map((account) => (
                <div className="account-row" key={account.name}>
                  <div>
                    <strong>{account.name}</strong>
                    <small>{account.provider}</small>
                  </div>
                  <span className={`status-chip ${statusClass(account.status)}`}>
                    {account.status}
                  </span>
                  <span>{account.findings} findings</span>
                  <strong>{account.risk}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="panel" id="scans" aria-labelledby="scans-title">
            <div className="panel-heading compact">
              <div>
                <p className="eyebrow">Execution</p>
                <h3 id="scans-title">Scan activity</h3>
              </div>
            </div>
            <div className="scan-list">
              {scans.map((scan) => (
                <div className="scan-row" key={scan.account}>
                  <span className={`scan-dot ${statusClass(scan.status)}`} aria-hidden="true" />
                  <div>
                    <strong>{scan.account}</strong>
                    <small>
                      {scan.status} · {scan.duration}
                    </small>
                  </div>
                  <span>{scan.findings}</span>
                </div>
              ))}
            </div>
          </section>
        </section>
      </section>
    </main>
  );
}

function statusClass(status: AccountRow["status"] | ScanRow["status"]) {
  return status.toLowerCase().replace(" ", "-");
}
