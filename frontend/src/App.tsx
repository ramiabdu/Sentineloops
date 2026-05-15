import { useMemo, useState, type FormEvent } from "react";

type DashboardView = "overview" | "accounts" | "findings";

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

type FindingSeverity = "Critical" | "High" | "Medium" | "Low";
type FindingStatus = "Open" | "Triaged" | "Resolved";

type FindingRow = {
  id: string;
  title: string;
  account: string;
  severity: FindingSeverity;
  status: FindingStatus;
  scanner: string;
  resourceType: string;
  region: string;
  risk: number;
  lastSeen: string;
  occurrenceCount: number;
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
    id: "fnd-001",
    title: "sg-09f3 allows public SSH",
    account: "AWS production",
    severity: "Critical",
    status: "Open",
    scanner: "Security group exposure",
    resourceType: "Security group",
    region: "us-east-1",
    risk: 10,
    lastSeen: "4m ago",
    occurrenceCount: 3,
  },
  {
    id: "fnd-002",
    title: "public-assets bucket ACL",
    account: "AWS production",
    severity: "High",
    status: "Open",
    scanner: "S3 public bucket",
    resourceType: "S3 bucket",
    region: "us-east-1",
    risk: 7.8,
    lastSeen: "12m ago",
    occurrenceCount: 2,
  },
  {
    id: "fnd-003",
    title: "alice console MFA missing",
    account: "AWS staging",
    severity: "Medium",
    status: "Triaged",
    scanner: "IAM without MFA",
    resourceType: "IAM user",
    region: "global",
    risk: 5.6,
    lastSeen: "18m ago",
    occurrenceCount: 1,
  },
  {
    id: "fnd-004",
    title: "staging-api allows public HTTPS",
    account: "AWS staging",
    severity: "High",
    status: "Open",
    scanner: "Security group exposure",
    resourceType: "Security group",
    region: "eu-central-1",
    risk: 7.2,
    lastSeen: "31m ago",
    occurrenceCount: 4,
  },
  {
    id: "fnd-005",
    title: "sandbox bucket public policy",
    account: "AWS sandbox",
    severity: "Medium",
    status: "Resolved",
    scanner: "S3 public bucket",
    resourceType: "S3 bucket",
    region: "us-west-2",
    risk: 4.8,
    lastSeen: "1h ago",
    occurrenceCount: 1,
  },
  {
    id: "fnd-006",
    title: "developer user MFA not enrolled",
    account: "AWS sandbox",
    severity: "Low",
    status: "Triaged",
    scanner: "IAM without MFA",
    resourceType: "IAM user",
    region: "global",
    risk: 3.4,
    lastSeen: "2h ago",
    occurrenceCount: 1,
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
  const [findingSearch, setFindingSearch] = useState("");
  const [findingSeverityFilter, setFindingSeverityFilter] = useState<FindingSeverity | "All">(
    "All",
  );
  const [findingStatusFilter, setFindingStatusFilter] = useState<FindingStatus | "All">("All");
  const [lastOnboardedAccount, setLastOnboardedAccount] = useState<string | null>(null);

  const metrics = useMemo(() => buildMetrics(accounts, findings), [accounts]);
  const filteredFindings = useMemo(
    () =>
      filterFindings(
        findings,
        findingSearch,
        findingSeverityFilter,
        findingStatusFilter,
      ),
    [findingSearch, findingSeverityFilter, findingStatusFilter],
  );
  const pageMeta = getPageMeta(activeView);

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
          <button
            className={activeView === "findings" ? "active" : undefined}
            type="button"
            onClick={() => setActiveView("findings")}
          >
            Findings
          </button>
          <button type="button">Scans</button>
        </nav>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">{pageMeta.eyebrow}</p>
            <h2>{pageMeta.title}</h2>
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
            ) : null}
            {activeView === "accounts" ? (
              <button className="primary-action" form="account-onboarding-form" type="submit">
                Add account
              </button>
            ) : null}
            {activeView === "findings" ? (
              <button className="primary-action" type="button">
                Export CSV
              </button>
            ) : null}
          </div>
        </header>

        {activeView === "overview" ? (
          <OverviewDashboard
            accounts={accounts}
            findings={findings}
            metrics={metrics}
            onOpenAccounts={() => setActiveView("accounts")}
            onOpenFindings={() => setActiveView("findings")}
          />
        ) : null}
        {activeView === "accounts" ? (
          <AccountsPage
            accounts={accounts}
            accountForm={accountForm}
            lastOnboardedAccount={lastOnboardedAccount}
            onSubmitAccount={submitAccount}
            onUpdateAccountForm={updateAccountForm}
          />
        ) : null}
        {activeView === "findings" ? (
          <FindingsPage
            findingSearch={findingSearch}
            filteredFindings={filteredFindings}
            severityFilter={findingSeverityFilter}
            statusFilter={findingStatusFilter}
            totalFindings={findings.length}
            onSearchChange={setFindingSearch}
            onSeverityFilterChange={setFindingSeverityFilter}
            onStatusFilterChange={setFindingStatusFilter}
          />
        ) : null}
      </section>
    </main>
  );
}

function OverviewDashboard({
  accounts,
  findings,
  metrics,
  onOpenAccounts,
  onOpenFindings,
}: {
  accounts: AccountRow[];
  findings: FindingRow[];
  metrics: MetricCard[];
  onOpenAccounts: () => void;
  onOpenFindings: () => void;
}) {
  const priorityFindings = findings
    .filter((finding) => finding.status !== "Resolved")
    .slice(0, 3);

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
            <button className="text-action" type="button" onClick={onOpenFindings}>
              View all
            </button>
          </div>

          <div className="finding-table" role="table" aria-label="Priority findings">
            <div className="table-head" role="row">
              <span role="columnheader">Resource</span>
              <span role="columnheader">Account</span>
              <span role="columnheader">Severity</span>
              <span role="columnheader">Last seen</span>
            </div>
            {priorityFindings.map((finding) => (
              <div className="table-row" role="row" key={finding.id}>
                <div role="cell">
                  <strong>{finding.title}</strong>
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

function FindingsPage({
  filteredFindings,
  findingSearch,
  severityFilter,
  statusFilter,
  totalFindings,
  onSearchChange,
  onSeverityFilterChange,
  onStatusFilterChange,
}: {
  filteredFindings: FindingRow[];
  findingSearch: string;
  severityFilter: FindingSeverity | "All";
  statusFilter: FindingStatus | "All";
  totalFindings: number;
  onSearchChange: (value: string) => void;
  onSeverityFilterChange: (value: FindingSeverity | "All") => void;
  onStatusFilterChange: (value: FindingStatus | "All") => void;
}) {
  return (
    <section className="findings-page">
      <section className="panel" aria-labelledby="findings-table-title">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">Detection queue</p>
            <h3 id="findings-table-title">Findings table</h3>
          </div>
          <span className="panel-count">
            {filteredFindings.length}/{totalFindings}
          </span>
        </div>

        <div className="filter-bar" aria-label="Finding filters">
          <label className="search-field">
            <span>Search</span>
            <input
              value={findingSearch}
              onChange={(event) => onSearchChange(event.target.value)}
            />
          </label>
          <label className="compact-field">
            <span>Severity</span>
            <select
              value={severityFilter}
              onChange={(event) =>
                onSeverityFilterChange(event.target.value as FindingSeverity | "All")
              }
            >
              <option>All</option>
              <option>Critical</option>
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </label>
          <label className="compact-field">
            <span>Status</span>
            <select
              value={statusFilter}
              onChange={(event) =>
                onStatusFilterChange(event.target.value as FindingStatus | "All")
              }
            >
              <option>All</option>
              <option>Open</option>
              <option>Triaged</option>
              <option>Resolved</option>
            </select>
          </label>
        </div>

        <div className="findings-table" role="table" aria-label="Security findings">
          <div className="findings-table-head" role="row">
            <span role="columnheader">Finding</span>
            <span role="columnheader">Account</span>
            <span role="columnheader">Severity</span>
            <span role="columnheader">Status</span>
            <span role="columnheader">Risk</span>
            <span role="columnheader">Last seen</span>
          </div>
          {filteredFindings.map((finding) => (
            <FindingTableRow finding={finding} key={finding.id} />
          ))}
          {filteredFindings.length === 0 ? (
            <div className="empty-state" role="row">
              No findings match the selected filters.
            </div>
          ) : null}
        </div>
      </section>
    </section>
  );
}

function FindingTableRow({ finding }: { finding: FindingRow }) {
  return (
    <div className="findings-table-row" role="row">
      <div className="finding-primary" role="cell">
        <strong>{finding.title}</strong>
        <small>
          {finding.resourceType} - {finding.scanner} - {finding.region}
        </small>
      </div>
      <span data-label="Account" role="cell">
        {finding.account}
      </span>
      <span
        className={`severity-pill ${finding.severity.toLowerCase()}`}
        data-label="Severity"
        role="cell"
      >
        {finding.severity}
      </span>
      <span className="status-cell" data-label="Status" role="cell">
        <span className={`status-chip ${statusClass(finding.status)}`}>
          {finding.status}
        </span>
      </span>
      <strong className="risk-score" data-label="Risk" role="cell">
        {finding.risk.toFixed(1)}
      </strong>
      <span data-label="Last seen" role="cell">
        {finding.lastSeen}
      </span>
    </div>
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

function buildMetrics(accounts: AccountRow[], allFindings: FindingRow[]): MetricCard[] {
  const openFindings = allFindings.filter((finding) => finding.status === "Open").length;
  const criticalFindings = allFindings.filter(
    (finding) => finding.severity === "Critical" && finding.status !== "Resolved",
  ).length;
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
      detail: `${openFindings} need review today`,
      tone: "warning",
    },
    {
      label: "Critical risk",
      value: String(criticalFindings),
      detail: "Critical open findings",
      tone: "danger",
    },
    { label: "Scan coverage", value: "92%", detail: "Last run 12 minutes ago", tone: "calm" },
  ];
}

function filterFindings(
  allFindings: FindingRow[],
  search: string,
  severity: FindingSeverity | "All",
  status: FindingStatus | "All",
) {
  const normalizedSearch = search.trim().toLowerCase();

  return allFindings.filter((finding) => {
    const matchesSearch =
      normalizedSearch.length === 0 ||
      [
        finding.title,
        finding.account,
        finding.scanner,
        finding.resourceType,
        finding.region,
      ].some((value) => value.toLowerCase().includes(normalizedSearch));
    const matchesSeverity = severity === "All" || finding.severity === severity;
    const matchesStatus = status === "All" || finding.status === status;

    return matchesSearch && matchesSeverity && matchesStatus;
  });
}

function getPageMeta(view: DashboardView) {
  if (view === "accounts") {
    return { eyebrow: "Account inventory", title: "Cloud accounts" };
  }
  if (view === "findings") {
    return { eyebrow: "Finding management", title: "Security findings" };
  }
  return { eyebrow: "Cloud security dashboard", title: "Security posture overview" };
}

function statusClass(status: AccountStatus | FindingStatus | ScanRow["status"]) {
  return status.toLowerCase().replace(" ", "-");
}
