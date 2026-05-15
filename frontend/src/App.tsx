import { useMemo, useState, type FormEvent } from "react";

type DashboardView = "overview" | "accounts";

type MetricCard = {
  label: string;
  value: string;
  detail: string;
  tone: "steady" | "warning" | "danger" | "calm";
};

type AccountStatus = "Active" | "Scanning" | "Needs review" | "Pending";
type Provider = "AWS" | "Azure" | "GCP";
type Environment = "Production" | "Staging" | "Sandbox";

type AccountRow = {
  name: string;
  provider: Provider;
  externalId: string;
  environment: Environment;
  status: AccountStatus;
  findings: number;
  risk: number;
  lastScan: string;
};

type AccountFormState = {
  name: string;
  provider: Provider;
  externalId: string;
  environment: Environment;
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

const initialAccounts: AccountRow[] = [
  {
    name: "AWS production",
    provider: "AWS",
    externalId: "123456789012",
    environment: "Production",
    status: "Scanning",
    findings: 14,
    risk: 84,
    lastScan: "Running",
  },
  {
    name: "AWS staging",
    provider: "AWS",
    externalId: "210987654321",
    environment: "Staging",
    status: "Active",
    findings: 7,
    risk: 58,
    lastScan: "12m ago",
  },
  {
    name: "AWS sandbox",
    provider: "AWS",
    externalId: "345678901234",
    environment: "Sandbox",
    status: "Needs review",
    findings: 3,
    risk: 41,
    lastScan: "1h ago",
  },
];

const initialAccountForm: AccountFormState = {
  name: "",
  provider: "AWS",
  externalId: "",
  environment: "Production",
};

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
  const [activeView, setActiveView] = useState<DashboardView>("overview");
  const [accounts, setAccounts] = useState(initialAccounts);
  const [accountForm, setAccountForm] = useState(initialAccountForm);
  const [lastOnboardedAccount, setLastOnboardedAccount] = useState<string | null>(null);

  const metrics = useMemo(() => buildMetrics(accounts), [accounts]);

  function updateAccountForm<Field extends keyof AccountFormState>(
    field: Field,
    value: AccountFormState[Field],
  ) {
    setAccountForm((current) => ({ ...current, [field]: value }));
  }

  function submitAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextAccount: AccountRow = {
      name: accountForm.name.trim(),
      provider: accountForm.provider,
      externalId: accountForm.externalId.trim(),
      environment: accountForm.environment,
      status: "Pending",
      findings: 0,
      risk: 0,
      lastScan: "Not scanned",
    };

    if (!nextAccount.name || !nextAccount.externalId) {
      return;
    }

    setAccounts((current) => [nextAccount, ...current]);
    setAccountForm(initialAccountForm);
    setLastOnboardedAccount(nextAccount.name);
  }

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
          <button
            className={activeView === "overview" ? "active" : undefined}
            type="button"
            onClick={() => setActiveView("overview")}
          >
            Overview
          </button>
          <button
            className={activeView === "accounts" ? "active" : undefined}
            type="button"
            onClick={() => setActiveView("accounts")}
          >
            Accounts
          </button>
          <button type="button">Findings</button>
          <button type="button">Scans</button>
        </nav>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">
              {activeView === "overview" ? "Cloud security dashboard" : "Account inventory"}
            </p>
            <h2>{activeView === "overview" ? "Security posture overview" : "Cloud accounts"}</h2>
          </div>
          <div className="header-actions" aria-label="Page controls">
            {activeView === "overview" ? (
              <>
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
              </>
            ) : (
              <button className="primary-action" form="account-onboarding-form" type="submit">
                Add account
              </button>
            )}
          </div>
        </header>

        {activeView === "overview" ? (
          <OverviewDashboard
            accounts={accounts}
            metrics={metrics}
            onOpenAccounts={() => setActiveView("accounts")}
          />
        ) : (
          <AccountsPage
            accounts={accounts}
            accountForm={accountForm}
            lastOnboardedAccount={lastOnboardedAccount}
            onSubmitAccount={submitAccount}
            onUpdateAccountForm={updateAccountForm}
          />
        )}
      </section>
    </main>
  );
}

function OverviewDashboard({
  accounts,
  metrics,
  onOpenAccounts,
}: {
  accounts: AccountRow[];
  metrics: MetricCard[];
  onOpenAccounts: () => void;
}) {
  return (
    <>
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
                <span className={`severity-pill ${finding.severity.toLowerCase()}`} role="cell">
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
            <button className="text-action" type="button" onClick={onOpenAccounts}>
              Manage
            </button>
          </div>
          <div className="account-list">
            {accounts.slice(0, 3).map((account) => (
              <AccountSummaryRow
                account={account}
                key={`${account.provider}-${account.externalId}`}
              />
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
                    {scan.status} - {scan.duration}
                  </small>
                </div>
                <span>{scan.findings}</span>
              </div>
            ))}
          </div>
        </section>
      </section>
    </>
  );
}

function AccountsPage({
  accounts,
  accountForm,
  lastOnboardedAccount,
  onSubmitAccount,
  onUpdateAccountForm,
}: {
  accounts: AccountRow[];
  accountForm: AccountFormState;
  lastOnboardedAccount: string | null;
  onSubmitAccount: (event: FormEvent<HTMLFormElement>) => void;
  onUpdateAccountForm: <Field extends keyof AccountFormState>(
    field: Field,
    value: AccountFormState[Field],
  ) => void;
}) {
  return (
    <section className="accounts-layout">
      <section className="panel onboarding-panel" aria-labelledby="onboarding-title">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">Onboarding</p>
            <h3 id="onboarding-title">Add cloud account</h3>
          </div>
        </div>

        <form className="account-form" id="account-onboarding-form" onSubmit={onSubmitAccount}>
          <label className="field">
            <span>Account name</span>
            <input
              required
              maxLength={80}
              value={accountForm.name}
              onChange={(event) => onUpdateAccountForm("name", event.target.value)}
            />
          </label>

          <div className="form-grid">
            <label className="field">
              <span>Provider</span>
              <select
                value={accountForm.provider}
                onChange={(event) =>
                  onUpdateAccountForm("provider", event.target.value as Provider)
                }
              >
                <option>AWS</option>
                <option>Azure</option>
                <option>GCP</option>
              </select>
            </label>

            <label className="field">
              <span>Environment</span>
              <select
                value={accountForm.environment}
                onChange={(event) =>
                  onUpdateAccountForm("environment", event.target.value as Environment)
                }
              >
                <option>Production</option>
                <option>Staging</option>
                <option>Sandbox</option>
              </select>
            </label>
          </div>

          <label className="field">
            <span>External account ID</span>
            <input
              required
              inputMode="numeric"
              maxLength={32}
              value={accountForm.externalId}
              onChange={(event) => onUpdateAccountForm("externalId", event.target.value)}
            />
          </label>

          {lastOnboardedAccount ? (
            <p className="form-status" role="status">
              {lastOnboardedAccount} added as pending.
            </p>
          ) : null}
        </form>
      </section>

      <section className="panel accounts-table-panel" aria-labelledby="accounts-table-title">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">Inventory</p>
            <h3 id="accounts-table-title">Managed accounts</h3>
          </div>
          <span className="panel-count">{accounts.length}</span>
        </div>

        <div className="accounts-table" role="table" aria-label="Managed cloud accounts">
          <div className="accounts-table-head" role="row">
            <span role="columnheader">Account</span>
            <span role="columnheader">Provider</span>
            <span role="columnheader">Status</span>
            <span role="columnheader">Findings</span>
            <span role="columnheader">Risk</span>
            <span role="columnheader">Last scan</span>
          </div>
          {accounts.map((account) => (
            <div
              className="accounts-table-row"
              role="row"
              key={`${account.provider}-${account.externalId}`}
            >
              <div role="cell">
                <strong>{account.name}</strong>
                <small>{account.externalId}</small>
              </div>
              <span data-label="Provider" role="cell">
                {account.provider}
              </span>
              <span className="status-cell" data-label="Status" role="cell">
                <span className={`status-chip ${statusClass(account.status)}`}>
                  {account.status}
                </span>
              </span>
              <span data-label="Findings" role="cell">
                {account.findings}
              </span>
              <strong data-label="Risk" role="cell">
                {account.risk}
              </strong>
              <span data-label="Last scan" role="cell">
                {account.lastScan}
              </span>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}

function AccountSummaryRow({ account }: { account: AccountRow }) {
  return (
    <div className="account-row">
      <div>
        <strong>{account.name}</strong>
        <small>
          {account.provider} - {account.environment}
        </small>
      </div>
      <span className={`status-chip ${statusClass(account.status)}`}>{account.status}</span>
      <span>{account.findings} findings</span>
      <strong>{account.risk}</strong>
    </div>
  );
}

function buildMetrics(accounts: AccountRow[]): MetricCard[] {
  const openFindings = accounts.reduce((total, account) => total + account.findings, 0);
  const criticalRiskAccounts = accounts.filter((account) => account.risk >= 80).length;
  const activeAccounts = accounts.filter((account) => account.status === "Active").length;

  return [
    {
      label: "Cloud accounts",
      value: String(accounts.length),
      detail: `${activeAccounts} active, ${accounts.length - activeAccounts} pending or scanning`,
      tone: "steady",
    },
    {
      label: "Open findings",
      value: String(openFindings),
      detail: "8 need review today",
      tone: "warning",
    },
    {
      label: "Critical risk",
      value: String(criticalRiskAccounts),
      detail: "Accounts at 80+ risk",
      tone: "danger",
    },
    { label: "Scan coverage", value: "92%", detail: "Last run 12 minutes ago", tone: "calm" },
  ];
}

function statusClass(status: AccountStatus | ScanRow["status"]) {
  return status.toLowerCase().replace(" ", "-");
}
