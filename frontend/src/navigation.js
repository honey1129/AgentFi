export const adminSections = [
  {
    section: "runtime",
    label: "Runtime",
    to: "/runtime",
    children: [
      { id: "overview", label: "Overview", to: "/runtime/overview" },
    ],
  },
  {
    section: "launchpad",
    label: "Launchpad",
    to: "/launchpad",
    children: [
      { id: "session", label: "Session", to: "/launchpad/session" },
      { id: "create", label: "Create Agent", to: "/launchpad/create" },
    ],
  },
  {
    section: "wallets",
    label: "Wallets",
    to: "/wallets",
    children: [
      { id: "registry", label: "Registry", to: "/wallets/registry" },
      { id: "operator", label: "Operator", to: "/wallets/operator" },
    ],
  },
  {
    section: "agents",
    label: "Agents",
    to: "/agents",
    children: [
      { id: "directory", label: "Directory", to: "/agents/library" },
    ],
  },
  {
    section: "market",
    label: "Market",
    to: "/market",
    children: [
      { id: "listings", label: "Listings", to: "/market/listings" },
      { id: "transfers", label: "Transfers", to: "/market/transfers" },
    ],
  },
  {
    section: "runs",
    label: "Runs",
    to: "/runs",
    children: [
      { id: "queue", label: "Queue", to: "/runs/queue" },
      { id: "history", label: "History", to: "/runs/history" },
      { id: "schedules", label: "Schedules", to: "/runs/schedules" },
    ],
  },
];

export const userSections = [
  {
    section: "home",
    label: "Home",
    to: "/app",
    children: [{ id: "home", label: "Workspace", to: "/app/home" }],
  },
  {
    section: "create",
    label: "New Agent",
    to: "/app/create",
    children: [{ id: "create", label: "New Agent", to: "/app/create" }],
  },
  {
    section: "agents",
    label: "Portfolio",
    to: "/app/agents",
    children: [{ id: "agents", label: "Portfolio", to: "/app/agents" }],
  },
  {
    section: "market",
    label: "Market",
    to: "/app/market",
    children: [
      { id: "market", label: "Listings", to: "/app/market" },
      { id: "transfers", label: "Transfers", to: "/app/transfers" },
    ],
  },
  {
    section: "runs",
    label: "Runs",
    to: "/app/runs",
    children: [{ id: "runs", label: "My Runs", to: "/app/runs" }],
  },
];
