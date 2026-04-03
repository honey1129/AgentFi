<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article v-for="item in networkMetrics" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.detail }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">System</p>
          <h2>Runtime Posture</h2>
        </div>
        <span class="panel-chip">{{ runtimeHealth }}</span>
      </header>
      <AdminStatusStrip :status-rows="statusRows" :network-metrics="[]" />
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Environment</p>
          <h2>Connection &amp; Chain</h2>
        </div>
      </header>
      <div class="stack-grid">
        <div class="surface-block">
          <p class="surface-kicker">Current Session</p>
          <h3 class="surface-title">Operator context</h3>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>MetaMask Address</dt>
              <dd>{{ store.state.metamask.address || "Not connected" }}</dd>
            </div>
            <div>
              <dt>Runtime Wallet</dt>
              <dd>{{ store.state.metamask.wallet?.name || store.state.metamask.wallet?.id || "Not mapped" }}</dd>
            </div>
            <div>
              <dt>Chain ID</dt>
              <dd>{{ store.state.metamask.chainId || "Unavailable" }}</dd>
            </div>
            <div>
              <dt>Session</dt>
              <dd>{{ store.authenticated.value ? "Signed" : "Unsigned" }}</dd>
            </div>
          </dl>
        </div>
        <div class="surface-block">
          <p class="surface-kicker">Ownership Sync</p>
          <h3 class="surface-title">Chain linkage</h3>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Contract</dt>
              <dd>{{ store.state.runtime?.nft_contract_address || "Not configured" }}</dd>
            </div>
            <div>
              <dt>Marketplace</dt>
              <dd>{{ store.state.runtime?.marketplace_contract_address || "Not configured" }}</dd>
            </div>
            <div>
              <dt>Chain Sync</dt>
              <dd>{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</dd>
            </div>
            <div>
              <dt>Auto Mint</dt>
              <dd>{{ store.state.runtime?.auto_onchain_mint_enabled ? "Enabled" : "Disabled" }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Navigation</p>
          <h2>Operational Domains</h2>
        </div>
      </header>
      <div class="entity-grid compact-entity-grid">
        <RouterLink
          v-for="link in quickLinks"
          :key="link.to"
          :to="link.to"
          class="entity-card overview-link-card"
        >
          <div class="entity-card-header">
            <strong>{{ link.label }}</strong>
            <span class="status-badge">{{ link.metric }}</span>
          </div>
          <p class="overview-link-copy">{{ link.description }}</p>
        </RouterLink>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Execution</p>
          <h2>Queue Health</h2>
        </div>
        <span class="panel-chip">{{ store.state.runMetrics?.queue_depth ?? 0 }} queued</span>
      </header>
      <div class="metric-strip metric-strip-embedded">
        <article class="metric-card">
          <span>Retry Pending</span>
          <strong>{{ store.state.runMetrics?.retry_pending_count ?? 0 }}</strong>
          <p>Queued runs that have already consumed at least one attempt.</p>
        </article>
        <article class="metric-card">
          <span>Cancel Requested</span>
          <strong>{{ store.state.runMetrics?.cancel_requested ?? 0 }}</strong>
          <p>Runs waiting for the worker to acknowledge cancellation.</p>
        </article>
        <article class="metric-card">
          <span>Average Duration</span>
          <strong>{{ averageDurationLabel }}</strong>
          <p>Derived from completed runs in the current dataset.</p>
        </article>
      </div>
      <dl class="detail-list detail-list-two">
        <div>
          <dt>Oldest Queued</dt>
          <dd>{{ store.formatDateTime(store.state.runMetrics?.oldest_queued_at) }}</dd>
        </div>
        <div>
          <dt>Event Stream Length</dt>
          <dd>{{ store.state.runMetrics?.event_stream_length ?? 0 }}</dd>
        </div>
        <div>
          <dt>Completed</dt>
          <dd>{{ store.state.runMetrics?.totals?.COMPLETED ?? 0 }}</dd>
        </div>
        <div>
          <dt>Failed / Timed Out</dt>
          <dd>{{ (store.state.runMetrics?.totals?.FAILED ?? 0) + (store.state.runMetrics?.totals?.TIMED_OUT ?? 0) }}</dd>
        </div>
      </dl>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Runtime Logs</p>
          <h2>Recent Events</h2>
        </div>
        <span class="panel-chip">{{ store.state.runtimeLogs.length }} entries</span>
      </header>
      <div v-if="!store.state.runtimeLogs.length" class="empty-state">
        No runtime events recorded yet.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head log-table">
          <span>Event</span>
          <span>Timestamp</span>
          <span>Payload</span>
        </div>
        <article v-for="entry in store.state.runtimeLogs" :key="entry.id" class="data-table-row log-table">
          <div class="table-cell">
            <strong>{{ entry.event_type }}</strong>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ store.formatDateTime(new Date(entry.timestamp_ms).toISOString()) }}</span>
          </div>
          <div class="table-cell">
            <pre class="code-block compact-code-block">{{ JSON.stringify(entry.fields, null, 2) }}</pre>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from "vue";

import AdminStatusStrip from "@/components/AdminStatusStrip.vue";
import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();

const currentWallet = computed(() => store.state.metamask.wallet);

const runtimeHealth = computed(() => {
  if (store.state.refreshing) {
    return "Syncing";
  }
  if (store.state.health?.status === "ok") {
    return "Healthy";
  }
  return "Check required";
});

const operatorSummary = computed(() => {
  if (store.authenticated.value && currentWallet.value) {
    return currentWallet.value.name || truncateAddress(currentWallet.value.chain_address || currentWallet.value.id, 18);
  }
  if (store.state.metamask.address) {
    return truncateAddress(store.state.metamask.address, 18);
  }
  return "Unsigned";
});

const chainSummary = computed(() => {
  const contract = store.state.runtime?.nft_contract_address;
  if (store.state.runtime?.chain_sync_state === "READY" && contract) {
    return `READY · ${truncateAddress(contract, 16)}`;
  }
  return store.state.runtime?.chain_sync_state || "DISABLED";
});

const statusRows = computed(() => [
  {
    label: "Runtime",
    value: runtimeHealth.value,
    detail: store.state.refreshing ? "Refreshing runtime snapshot from API." : "FastAPI, MySQL, Redis, and workers are currently reachable.",
    tone: store.state.health?.status === "ok" ? "positive" : "neutral",
  },
  {
    label: "Operator",
    value: operatorSummary.value,
    detail: store.authenticated.value
      ? "This browser session can submit protected runtime writes."
      : "Read access is open, but write actions remain locked until sign-in.",
    tone: store.authenticated.value ? "positive" : "neutral",
  },
  {
    label: "Session",
    value: "Overview",
    detail: "This dedicated route holds the shared system snapshot for the admin console.",
    tone: "neutral",
  },
  {
    label: "Chain",
    value: chainSummary.value,
    detail: store.state.runtime?.chain_sync_enabled
      ? "Ownership can follow ERC-721 transfer events for the configured contract."
      : "No active on-chain ownership sync is configured for this runtime.",
    tone: store.state.runtime?.chain_sync_enabled ? "positive" : "neutral",
  },
]);

const networkMetrics = computed(() => [
  {
    label: "Wallets",
    value: store.state.wallets.length,
    detail: "Runtime identities currently known to the backend.",
  },
  {
    label: "Agents",
    value: store.state.agents.length,
    detail: "NFT-backed agent records in the current runtime.",
  },
  {
    label: "Listings",
    value: store.state.listings.length,
    detail: "Open ownership listings still awaiting settlement.",
  },
  {
    label: "Runs",
    value: store.state.runs.length,
    detail: `${store.queuedRuns.value.length} queued · ${store.runningRuns.value.length} running · ${store.completedRuns.value.length} completed`,
  },
]);

const quickLinks = computed(() => [
  {
    label: "Launchpad",
    to: "/launchpad/session",
    metric: store.authenticated.value ? "Signed" : "Unsigned",
    description: "Handle MetaMask connection, challenge signing, and agent creation.",
  },
  {
    label: "Wallets",
    to: "/wallets/registry",
    metric: `${store.state.wallets.length}`,
    description: "Inspect runtime identities, chain addresses, and wallet balances.",
  },
  {
    label: "Agents",
    to: "/agents/library",
    metric: `${store.state.agents.length}`,
    description: "Review agent ownership, prompt state, and NFT sync mode.",
  },
  {
    label: "Market",
    to: "/market/listings",
    metric: `${store.state.listings.length}`,
    description: "Open listings, buy control, and inspect live ownership inventory.",
  },
  {
    label: "Runs",
    to: "/runs/queue",
    metric: `${store.state.runs.length}`,
    description: "Queue work, inspect execution history, and manage schedules.",
  },
]);

const averageDurationLabel = computed(() => {
  const value = store.state.runMetrics?.average_duration_seconds;
  if (value === null || value === undefined) {
    return "No data";
  }
  if (value < 60) {
    return `${value}s`;
  }
  const minutes = Math.floor(value / 60);
  const seconds = Math.round(value % 60);
  return seconds ? `${minutes}m ${seconds}s` : `${minutes}m`;
});

function truncateAddress(value, size = 14) {
  if (!value) {
    return "Unavailable";
  }
  if (value.length <= size) {
    return value;
  }
  return `${value.slice(0, Math.max(6, size - 7))}...${value.slice(-4)}`;
}
</script>
