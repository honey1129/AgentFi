export const workspaceSections = [
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
