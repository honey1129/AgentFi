import { createRouter, createWebHistory } from "vue-router";

import AgentDetailPage from "@/pages/AgentDetailPage.vue";
import AgentsPage from "@/pages/AgentsPage.vue";
import LaunchpadCreatePage from "@/pages/LaunchpadCreatePage.vue";
import LaunchpadPage from "@/pages/LaunchpadPage.vue";
import ListingDetailPage from "@/pages/ListingDetailPage.vue";
import MarketTransfersPage from "@/pages/MarketTransfersPage.vue";
import MarketPage from "@/pages/MarketPage.vue";
import RuntimeOverviewPage from "@/pages/RuntimeOverviewPage.vue";
import RunDetailPage from "@/pages/RunDetailPage.vue";
import RunsHistoryPage from "@/pages/RunsHistoryPage.vue";
import RunsPage from "@/pages/RunsPage.vue";
import ScheduleDetailPage from "@/pages/ScheduleDetailPage.vue";
import RunsSchedulesPage from "@/pages/RunsSchedulesPage.vue";
import WalletDetailPage from "@/pages/WalletDetailPage.vue";
import WalletOperatorPage from "@/pages/WalletOperatorPage.vue";
import WalletsPage from "@/pages/WalletsPage.vue";

const routes = [
  {
    path: "/",
    redirect: "/runtime/overview",
  },
  {
    path: "/dashboard",
    redirect: "/runtime/overview",
  },
  {
    path: "/runtime",
    redirect: "/runtime/overview",
  },
  {
    path: "/runtime/overview",
    name: "runtime-overview",
    component: RuntimeOverviewPage,
    meta: {
      section: "runtime",
      subsection: "overview",
      eyebrow: "Runtime Overview",
      title: "Overview",
      headline: "Monitor runtime health, operator access, chain posture, and registry counts from one dedicated system page.",
      description: "This route holds the global platform snapshot so the rest of the workspace can stay focused on route-specific actions instead of repeating the same summary strip.",
      summaryTitle: "Overview",
      summaryBody: "Use this page as the system home. It concentrates platform-level status and count signals into one place.",
    },
  },
  {
    path: "/launchpad",
    redirect: "/launchpad/session",
  },
  {
    path: "/launchpad/session",
    name: "launchpad",
    component: LaunchpadPage,
    meta: {
      section: "launchpad",
      subsection: "session",
      eyebrow: "Agent Ownership Runtime",
      title: "Session",
      headline: "Connect MetaMask and bind the current operator to the runtime.",
      description: "Keep wallet connection, session signature, and runtime readiness on a dedicated onboarding page before moving into agent creation or trading.",
      summaryTitle: "Authentication",
      summaryBody: "This page is only about operator identity and runtime access. It narrows the first step into one clear handshake.",
    },
  },
  {
    path: "/launchpad/create",
    name: "launchpad-create",
    component: LaunchpadCreatePage,
    meta: {
      section: "launchpad",
      subsection: "create",
      eyebrow: "Agent Ownership Runtime",
      title: "Create Agent",
      headline: "Mint a new agent and bind its control plane to a dedicated ownership NFT.",
      description: "Separate agent creation from authentication so minting, token mapping, and prompt setup live on their own page.",
      summaryTitle: "Creation",
      summaryBody: "Use this page after the operator session is ready. It is focused on prompt setup, ownership minting, and initial agent shape.",
    },
  },
  {
    path: "/wallets",
    redirect: "/wallets/registry",
  },
  {
    path: "/wallets/registry",
    name: "wallets",
    component: WalletsPage,
    meta: {
      section: "wallets",
      subsection: "registry",
      eyebrow: "Wallet Registry",
      title: "Registry",
      headline: "Inspect runtime wallets, chain addresses, and balances.",
      description: "Use a dedicated registry view for linked wallets instead of mixing identity, execution, and trade actions on one screen.",
      summaryTitle: "Registry",
      summaryBody: "This page is read-heavy on purpose. It is for checking the operator identity map, not for driving agent execution or trades.",
    },
  },
  {
    path: "/wallets/operator",
    name: "wallets-operator",
    component: WalletOperatorPage,
    meta: {
      section: "wallets",
      subsection: "operator",
      eyebrow: "Operator Session",
      title: "Operator",
      headline: "Review the active MetaMask session and the runtime wallet it maps to.",
      description: "Keep connected account state, chain information, and session controls on a page dedicated to the current operator identity.",
      summaryTitle: "Operator",
      summaryBody: "This page keeps the current session in view after onboarding so you can verify who is actually driving runtime writes.",
    },
  },
  {
    path: "/wallets/:walletId",
    name: "wallet-detail",
    component: WalletDetailPage,
    meta: {
      section: "wallets",
      subsection: "registry",
      eyebrow: "Wallet Profile",
      title: "Wallet Detail",
      headline: "Inspect one runtime wallet across ownership, listings, and execution activity.",
      description: "This page promotes wallet inspection into its own detail view so you can trace one operator identity through the whole runtime.",
      summaryTitle: "Identity",
      summaryBody: "Owned agents, seller activity, and requested runs are grouped around one wallet instead of being flattened into the registry list.",
    },
  },
  {
    path: "/agents",
    redirect: "/agents/library",
  },
  {
    path: "/agents/library",
    name: "agents",
    component: AgentsPage,
    meta: {
      section: "agents",
      subsection: "directory",
      eyebrow: "Agent Registry",
      title: "Directory",
      headline: "Review agent ownership, sync mode, and prompt state.",
      description: "Use the directory for scanning the fleet. Deep inspection moves into a dedicated agent detail route instead of a crowded list page.",
      summaryTitle: "Ownership",
      summaryBody: "This page is for browsing the inventory. Detailed prompt, metadata, and run history live on a dedicated agent page.",
    },
  },
  {
    path: "/agents/:agentId",
    name: "agent-detail",
    component: AgentDetailPage,
    meta: {
      section: "agents",
      subsection: "directory",
      eyebrow: "Agent Profile",
      title: "Agent Detail",
      headline: "Inspect one agent in depth, including metadata, ownership, prompt, and run history.",
      description: "This route promotes the detail view into a full page so the runtime no longer relies on a drawer for all deep inspection work.",
      summaryTitle: "Profile",
      summaryBody: "Owner, tokenURI, prompt, and execution history are grouped around one agent rather than competing with the whole directory.",
    },
  },
  {
    path: "/market",
    redirect: "/market/listings",
  },
  {
    path: "/market/listings",
    name: "market",
    component: MarketPage,
    meta: {
      section: "market",
      subsection: "listings",
      eyebrow: "Ownership Market",
      title: "Listings",
      headline: "Open and buy listings from the market workspace.",
      description: "Listings and purchases stay on one page so market inventory, spotlight cards, and pricing actions stay tightly grouped.",
      summaryTitle: "Listings",
      summaryBody: "This page is about sale inventory, current holder visibility, and buy flows. Direct NFT transfers move to their own route.",
    },
  },
  {
    path: "/market/transfers",
    name: "market-transfers",
    component: MarketTransfersPage,
    meta: {
      section: "market",
      subsection: "transfers",
      eyebrow: "Ownership Transfer",
      title: "Transfers",
      headline: "Move NFT ownership directly without going through a listing flow.",
      description: "This route is for direct handoff. It keeps transfer rules, chain sync mode, and owned inventory separate from market pricing.",
      summaryTitle: "Transfers",
      summaryBody: "Use this page when the operator already knows the destination address and wants a direct ownership move instead of a sale.",
    },
  },
  {
    path: "/market/listings/:listingId",
    name: "listing-detail",
    component: ListingDetailPage,
    meta: {
      section: "market",
      subsection: "listings",
      eyebrow: "Listing Detail",
      title: "Listing Detail",
      headline: "Inspect one sale listing with holder context, token metadata, and linked agent information.",
      description: "This page keeps pricing, seller, current holder, and token identity together so market review can go deeper than the listing board.",
      summaryTitle: "Listing",
      summaryBody: "Use this page for one listing at a time, especially when you need to verify owner drift or jump into the linked agent profile.",
    },
  },
  {
    path: "/marketplace",
    redirect: "/market/listings",
  },
  {
    path: "/runs",
    redirect: "/runs/queue",
  },
  {
    path: "/runs/queue",
    name: "runs",
    component: RunsPage,
    meta: {
      section: "runs",
      subsection: "queue",
      eyebrow: "Execution Workspace",
      title: "Queue",
      headline: "Submit new work and watch the live execution lane.",
      description: "Queueing deserves its own page so task submission and live execution pressure are visible without schedule setup or deep history noise.",
      summaryTitle: "Queue",
      summaryBody: "This page focuses on near-term execution: what is waiting, what is running, and which operator is sending work into the lane.",
    },
  },
  {
    path: "/runs/history",
    name: "runs-history",
    component: RunsHistoryPage,
    meta: {
      section: "runs",
      subsection: "history",
      eyebrow: "Execution History",
      title: "History",
      headline: "Review finished and in-flight runs as a dedicated execution log.",
      description: "This route turns run history into a standalone page so outputs, requesters, and run status are easier to scan over time.",
      summaryTitle: "History",
      summaryBody: "Use this page when you want playback and post-run inspection rather than queue submission or scheduling.",
    },
  },
  {
    path: "/runs/history/:runId",
    name: "run-detail",
    component: RunDetailPage,
    meta: {
      section: "runs",
      subsection: "history",
      eyebrow: "Run Detail",
      title: "Run Detail",
      headline: "Inspect one execution record in full, including input, output, requester, and status.",
      description: "This page turns a run into a dedicated artifact so you can review the full output without keeping the whole history list expanded.",
      summaryTitle: "Playback",
      summaryBody: "Use this page when one run matters more than the whole feed and you need a cleaner view of its inputs and outputs.",
    },
  },
  {
    path: "/runs/schedules",
    name: "runs-schedules",
    component: RunsSchedulesPage,
    meta: {
      section: "runs",
      subsection: "schedules",
      eyebrow: "Execution Automation",
      title: "Schedules",
      headline: "Configure recurring work without sharing space with ad hoc queueing.",
      description: "Schedule creation and existing automation records are kept on a page dedicated to timed execution rather than immediate runs.",
      summaryTitle: "Schedules",
      summaryBody: "This page is for interval-based dispatch. One-off work should stay on the queue page, and historical playback should stay in history.",
    },
  },
  {
    path: "/runs/schedules/:scheduleId",
    name: "schedule-detail",
    component: ScheduleDetailPage,
    meta: {
      section: "runs",
      subsection: "schedules",
      eyebrow: "Schedule Detail",
      title: "Schedule Detail",
      headline: "Inspect one automation rule with its timing, task template, and linked agent.",
      description: "This route gives scheduled work its own detail page so it is easier to reason about recurring dispatch than from a compact grid card.",
      summaryTitle: "Automation",
      summaryBody: "Use this page when you need to inspect one interval rule closely, especially before changing the linked agent or task template.",
    },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});
