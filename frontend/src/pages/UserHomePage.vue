<template>
  <div class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>Portfolio value</span>
        <strong>{{ portfolioValueDisplay }}</strong>
        <p><em class="wallet-home-kpi-move" :class="trendTone(portfolioDailyChangeValue)">{{ portfolioDailyChangeValueDisplay }} · {{ portfolioDailyChangePctDisplay }}</em></p>
      </article>
      <article class="wallet-page-kpi">
        <span>Listed value</span>
        <strong>{{ listedValueDisplay }}</strong>
        <p>{{ listedAgents.length }} operators currently exposed through the market route.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Unlisted value</span>
        <strong>{{ unlistedValueDisplay }}</strong>
        <p>{{ ownedAgents.length - listedAgents.length }} held operators still routing directly from the wallet.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Session</span>
        <strong>{{ sessionSummary }}</strong>
        <p>{{ sessionCopy }}</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Portfolio</p>
              <h2>Wallet overview</h2>
            </div>
            <div class="wallet-card-actions">
              <button class="wallet-home-primary" type="button" @click="router.push('/app/create')">New Agent</button>
              <button class="wallet-home-secondary" type="button" @click="router.push('/app/runs')">Runs</button>
              <button class="wallet-home-secondary" type="button" @click="router.push('/app/market')">Market</button>
              <button class="wallet-home-secondary" type="button" @click="router.push('/app/transfers')">Transfer</button>
            </div>
          </header>

          <p class="wallet-card-copy">
            Estimated operator value across owned agents, live listings, and current runtime demand.
          </p>

          <div class="wallet-home-balance-strip">
            <div class="wallet-home-balance-main">
              <span>Total portfolio value</span>
              <strong>{{ portfolioValueDisplay }}</strong>
              <div class="wallet-home-balance-move" :class="trendTone(portfolioDailyChangeValue)">
                <span>{{ portfolioDailyChangeValueDisplay }}</span>
                <span>{{ portfolioDailyChangePctDisplay }} in 24h</span>
              </div>
            </div>
            <div class="wallet-home-balance-side">
              <div class="wallet-home-balance-metric">
                <span>Listed</span>
                <strong>{{ listedValueDisplay }}</strong>
              </div>
              <div class="wallet-home-balance-metric">
                <span>Unlisted</span>
                <strong>{{ unlistedValueDisplay }}</strong>
              </div>
              <div class="wallet-home-balance-metric">
                <span>Active runs</span>
                <strong>{{ activeRuns.length }}</strong>
              </div>
            </div>
          </div>

          <div class="wallet-home-chart-block">
            <div class="wallet-home-chart-head">
              <div class="wallet-home-chart-label">Portfolio performance</div>
              <div class="wallet-home-chart-ranges">
                <button v-for="range in chartRanges" :key="range" type="button" :class="{ 'is-active': range === '1M' }">
                  {{ range }}
                </button>
              </div>
            </div>
            <div class="wallet-home-chart">
              <div
                v-for="(bar, index) in chartBars"
                :key="`${bar}-${index}`"
                class="wallet-home-chart-bar"
                :class="{ 'is-active': index === chartBars.length - 1 }"
                :style="{ height: `${bar}px` }"
              />
            </div>
          </div>

          <div class="wallet-home-meta-row">
            <div>
              <span>Wallets</span>
              <strong>{{ currentWalletId ? "1 selected" : "0 selected" }}</strong>
            </div>
            <div>
              <span>Top mover</span>
              <strong>{{ topMover ? topMover.name : "No mover" }}</strong>
              <em class="wallet-home-meta-trend" :class="topMover ? trendTone(topMover.changePct) : ''">{{ topMover ? topMover.changePctDisplay : "0.00%" }}</em>
            </div>
            <div>
              <span>Weakest</span>
              <strong>{{ weakestMover ? weakestMover.name : "No mover" }}</strong>
              <em class="wallet-home-meta-trend" :class="weakestMover ? trendTone(weakestMover.changePct) : ''">{{ weakestMover ? weakestMover.changePctDisplay : "0.00%" }}</em>
            </div>
            <div>
              <span>Network</span>
              <strong>{{ chainLabel }}</strong>
            </div>
          </div>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Portfolio</p>
              <h2>Portfolio assets</h2>
            </div>
            <div class="wallet-home-tabs">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                type="button"
                :class="{ 'is-active': activeTab === tab.id }"
                @click="activeTab = tab.id"
              >
                {{ tab.label }}
              </button>
            </div>
          </header>

          <p class="wallet-card-copy">
            Follow owned operator exposure, NFT surfaces, and wallet activity from a single asset lane.
          </p>

          <div class="wallet-home-table-shell">
            <template v-if="activeTab === 'agents'">
              <div class="wallet-home-table-head wallet-home-agent-table">
                <div>Agent</div>
                <div>Exposure</div>
                <div>24h</div>
                <div>Status</div>
                <div>Route</div>
              </div>

              <div
                v-for="asset in agentPortfolioRows"
                :key="asset.id"
                class="wallet-home-table-row wallet-home-agent-table"
              >
                <div class="wallet-home-agent-cell">
                  <div class="wallet-home-token-badge">{{ buildInitials(asset.name) }}</div>
                  <div>
                    <strong>{{ asset.name }}</strong>
                    <span>{{ asset.tokenLabel }} · {{ asset.syncLabel }}</span>
                  </div>
                </div>
                <div class="wallet-home-value-cell">
                  <strong>{{ asset.valueDisplay }}</strong>
                  <span>{{ asset.weightDisplay }} of portfolio</span>
                </div>
                <div class="wallet-home-change-cell" :class="trendTone(asset.changePct)">
                  <strong>{{ asset.changePctDisplay }}</strong>
                  <span>{{ asset.changeValueDisplay }}</span>
                </div>
                <div class="wallet-home-status-cell">
                  <strong>{{ asset.statusLabel }}</strong>
                  <span>{{ asset.statusCopy }}</span>
                </div>
                <div class="wallet-home-inline-meta">
                  <span :class="{ positive: asset.listed }">
                    {{ asset.listed ? "Market" : "Wallet" }}
                  </span>
                  <RouterLink :to="`/app/agents/${asset.id}`">View</RouterLink>
                </div>
              </div>

              <div v-if="!agentPortfolioRows.length" class="empty-state">
                No owned agents yet. Create your first operator from the new agent flow.
              </div>
            </template>

            <div v-else-if="activeTab === 'nfts'" class="wallet-home-nft-grid">
              <article v-for="agent in ownedAgents.slice(0, 4)" :key="agent.id" class="wallet-home-nft-card">
                <div class="wallet-home-nft-media">
                  <img
                    v-if="agent.nft.token_id"
                    :src="buildNftImageUrl(agent.nft.token_id)"
                    :alt="`${agent.name} preview`"
                  />
                  <div v-else class="wallet-home-nft-placeholder">{{ buildInitials(agent.name) }}</div>
                </div>
                <div class="wallet-home-nft-copy">
                  <strong>{{ agent.name }}</strong>
                  <span>{{ chainLabel }}</span>
                  <div class="wallet-home-nft-floor">Token {{ agent.nft.chain_token_id || agent.nft.token_id }}</div>
                </div>
              </article>

              <div v-if="!ownedAgents.length" class="empty-state">
                Mint an agent to populate your NFT inventory.
              </div>
            </div>

            <template v-else>
              <article
                v-for="item in activityItems"
                :key="item.title"
                class="wallet-home-activity-row"
              >
                <div>
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.meta }}</span>
                </div>
                <span class="wallet-status-pill" :class="activityTone(item.status)">
                  {{ item.status }}
                </span>
              </article>

              <div v-if="!activityItems.length" class="empty-state">
                No portfolio activity has been recorded for this wallet yet.
              </div>
            </template>
          </div>
        </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Wallet &amp; runtime</div>
          <div class="wallet-side-list">
            <div>
              <strong>Accounts</strong>
              <span>{{ currentWalletId ? "Main operator" : "No wallet connected" }}</span>
            </div>
            <div>
              <strong>Runtime wallet</strong>
              <span>{{ runtimeWalletLabel }}</span>
            </div>
            <div>
              <strong>Active network</strong>
              <span>{{ chainLabel }}</span>
            </div>
            <div>
              <strong>Watch route</strong>
              <span>{{ walletDisplay }}</span>
            </div>
          </div>
          <div class="wallet-side-actions-row">
            <button class="wallet-home-primary" type="button" @click="handleWalletAction">{{ walletActionLabel }}</button>
            <button class="wallet-home-secondary" type="button" @click="router.push('/app/create')">New Agent</button>
          </div>
        </article>

        <article class="wallet-side-card">
          <div class="wallet-side-title">Day movers</div>
          <div class="wallet-side-feed">
            <article v-for="asset in dayMovers" :key="asset.id" class="wallet-side-feed-row">
              <div>
                <strong>{{ asset.name }}</strong>
                <span>{{ asset.valueDisplay }} · {{ asset.weightDisplay }}</span>
              </div>
              <div class="wallet-side-trend" :class="trendTone(asset.changePct)">
                <strong>{{ asset.changePctDisplay }}</strong>
                <span>{{ asset.changeValueDisplay }}</span>
              </div>
            </article>
            <div v-if="!dayMovers.length" class="wallet-side-empty">No assets are available to track movement yet.</div>
          </div>
        </article>

        <article class="wallet-side-card">
          <div class="wallet-side-title">Permissions &amp; security</div>
          <div class="wallet-side-feed">
            <article v-for="item in securityItems" :key="item.title" class="wallet-side-feed-row is-dense">
              <div>
                <strong>{{ item.title }}</strong>
                <span>{{ item.desc }}</span>
              </div>
              <span class="wallet-status-pill" :class="item.tone === 'good' ? 'is-completed' : 'is-review'">
                {{ item.tone === "good" ? "Ready" : "Review" }}
              </span>
            </article>
          </div>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const router = useRouter();
const store = useRuntimeStore();
const activeTab = ref("agents");

const currentWalletId = computed(() => store.state.metamask.wallet?.id || null);
const ownedAgents = computed(() =>
  currentWalletId.value ? store.state.agents.filter((agent) => agent.nft.owner_wallet_id === currentWalletId.value) : []
);
const listedTokenIds = computed(() => new Set(store.state.listings.map((listing) => listing.token_id)));
const listedAgents = computed(() => ownedAgents.value.filter((agent) => listedTokenIds.value.has(agent.nft.token_id)));
const listingsByTokenId = computed(() => {
  const map = new Map();
  for (const listing of store.state.listings) {
    if (listing.token_id) {
      map.set(listing.token_id, listing);
    }
  }
  return map;
});
const myRuns = computed(() =>
  currentWalletId.value
    ? [...store.state.runs]
        .filter((run) => run.requested_by_wallet_id === currentWalletId.value)
        .sort((left, right) => Date.parse(right.queued_at || right.started_at || 0) - Date.parse(left.queued_at || left.started_at || 0))
    : []
);
const activeRuns = computed(() => myRuns.value.filter((run) => !store.isTerminalRun(run)));
const runsByAgentId = computed(() => {
  const map = new Map();
  for (const run of myRuns.value) {
    map.set(run.agent_id, (map.get(run.agent_id) || 0) + 1);
  }
  return map;
});

const walletDisplay = computed(
  () =>
    store.state.metamask.address
      ? store.truncate(store.state.metamask.address, 18)
      : store.state.metamask.wallet?.name || store.state.metamask.wallet?.id || "Wallet not connected"
);
const runtimeWalletLabel = computed(() => store.state.metamask.wallet?.name || store.state.metamask.wallet?.id || "Not mapped");
const chainLabel = computed(() => store.getRuntimeChainLabel());
const walletActionLabel = computed(() => {
  if (!store.state.metamask.address) {
    return "Connect wallet";
  }
  if (!store.authenticated.value) {
    return "Sign session";
  }
  return "Refresh workspace";
});
const sessionSummary = computed(() => {
  if (!store.state.metamask.address) {
    return "Disconnected";
  }
  if (!store.authenticated.value) {
    return "Unsigned";
  }
  return "Ready";
});
const sessionCopy = computed(() => {
  if (!store.state.metamask.address) {
    return "Connect a wallet to unlock minting, runs, and market routes.";
  }
  if (!store.authenticated.value) {
    return "Sign a challenge to activate protected runtime actions.";
  }
  return "Wallet session is authenticated and ready for protected actions.";
});

const agentPortfolioRows = computed(() => {
  const rows = ownedAgents.value.map((agent, index) => {
    const listing = listingsByTokenId.value.get(agent.nft.token_id);
    const hashed = hashValue(agent.id || agent.nft.token_id || index);
    const listingPrice = Number.parseFloat(listing?.price || "");
    const baseValue =
      Number.isFinite(listingPrice) && listingPrice > 0
        ? listingPrice
        : 320 + (hashed % 260) + (agent.nft.sync_mode === "CHAIN_SYNCED" ? 180 : 90) + ((runsByAgentId.value.get(agent.id) || 0) * 42);
    const changePct = ((hashed % 180) - 80) / 20;
    const changeValue = (baseValue * changePct) / 100;
    const listed = listedTokenIds.value.has(agent.nft.token_id);

    return {
      id: agent.id,
      name: agent.name,
      tokenLabel: agent.nft.chain_token_id || agent.nft.token_id,
      syncLabel: store.formatSyncMode(agent.nft.sync_mode),
      value: baseValue,
      valueDisplay: formatUsd(baseValue),
      changePct,
      changePctDisplay: formatSignedPercent(changePct),
      changeValue,
      changeValueDisplay: formatSignedUsd(changeValue),
      listed,
      statusLabel: listed ? "Listed" : "Idle",
      statusCopy: agent.status,
    };
  });

  const total = rows.reduce((sum, row) => sum + row.value, 0) || 1;
  return rows
    .map((row) => ({
      ...row,
      weight: row.value / total,
      weightDisplay: `${Math.round((row.value / total) * 100)}%`,
    }))
    .sort((left, right) => right.value - left.value);
});

const portfolioValue = computed(() => agentPortfolioRows.value.reduce((sum, row) => sum + row.value, 0));
const portfolioDailyChangeValue = computed(() => agentPortfolioRows.value.reduce((sum, row) => sum + row.changeValue, 0));
const portfolioDailyChangePct = computed(() => {
  if (!portfolioValue.value) {
    return 0;
  }
  return (portfolioDailyChangeValue.value / portfolioValue.value) * 100;
});
const listedValue = computed(() => agentPortfolioRows.value.filter((row) => row.listed).reduce((sum, row) => sum + row.value, 0));
const unlistedValue = computed(() => Math.max(0, portfolioValue.value - listedValue.value));
const topMover = computed(() =>
  agentPortfolioRows.value.length ? [...agentPortfolioRows.value].sort((left, right) => right.changePct - left.changePct)[0] : null
);
const weakestMover = computed(() =>
  agentPortfolioRows.value.length ? [...agentPortfolioRows.value].sort((left, right) => left.changePct - right.changePct)[0] : null
);
const dayMovers = computed(() => [...agentPortfolioRows.value].sort((left, right) => Math.abs(right.changePct) - Math.abs(left.changePct)).slice(0, 3));

const portfolioValueDisplay = computed(() => formatUsd(portfolioValue.value));
const portfolioDailyChangeValueDisplay = computed(() => formatSignedUsd(portfolioDailyChangeValue.value));
const portfolioDailyChangePctDisplay = computed(() => formatSignedPercent(portfolioDailyChangePct.value));
const listedValueDisplay = computed(() => formatUsd(listedValue.value));
const unlistedValueDisplay = computed(() => formatUsd(unlistedValue.value));

const tabs = [
  { id: "agents", label: "Agents" },
  { id: "nfts", label: "NFTs" },
  { id: "activity", label: "Activity" },
];

const chartRanges = ["1D", "1W", "1M", "1Y"];
const chartBars = computed(() => {
  const base = [42, 48, 45, 59, 61, 58, 65, 69, 66, 74, 78, 84];
  return base.map((value, index) => {
    const modifier = ownedAgents.value.length ? Math.min(ownedAgents.value.length * 2, 14) : 0;
    const runModifier = myRuns.value.length ? Math.min(Math.floor(myRuns.value.length / 2), 10) : 0;
    return Math.max(32, value + modifier + (index % 3 === 0 ? runModifier : 0));
  });
});

const activityItems = computed(() => {
  const runItems = myRuns.value.slice(0, 3).map((run) => ({
    title: `${store.findAgentById(run.agent_id)?.name || run.agent_id} run submitted`,
    meta: `${chainLabel.value} · ${store.formatDateTime(run.queued_at)}`,
    status: normalizeStatus(run.status),
  }));

  const listingItems = listedAgents.value.slice(0, 1).map((agent) => ({
    title: `${agent.name} listing is live`,
    meta: `${chainLabel.value} · ownership listed`,
    status: "Completed",
  }));

  return [...runItems, ...listingItems];
});

const securityItems = computed(() => [
  {
    title: store.authenticated.value ? "Signed session active" : "Unsigned wallet session",
    desc: store.authenticated.value
      ? "The current wallet can perform protected actions across creation, runs, and market routes."
      : "Sign a challenge before minting, listing, or transferring ownership.",
    tone: store.authenticated.value ? "good" : "warn",
  },
  {
    title: store.state.runtime?.chain_sync_enabled ? "Runtime chain sync enabled" : "Chain sync unavailable",
    desc: store.state.runtime?.chain_sync_enabled
      ? `${chainLabel.value} ownership is synchronized back into the runtime.`
      : "This environment is not currently reading onchain ownership state.",
    tone: store.state.runtime?.chain_sync_enabled ? "good" : "warn",
  },
  {
    title: store.state.runtime?.marketplace_contract_address ? "Marketplace route configured" : "Marketplace route missing",
    desc: store.state.runtime?.marketplace_contract_address
      ? "Listing and buy flows can route through the configured marketplace contract."
      : "No marketplace contract is configured for this runtime.",
    tone: store.state.runtime?.marketplace_contract_address ? "good" : "warn",
  },
]);

function buildInitials(value) {
  const source = String(value || "AF").trim();
  if (!source) {
    return "AF";
  }
  return source
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("")
    .slice(0, 2);
}

function hashValue(value) {
  const source = String(value || "agentfi");
  let hash = 0;
  for (const char of source) {
    hash = (hash * 31 + char.charCodeAt(0)) % 10007;
  }
  return hash;
}

function formatUsd(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function formatSignedUsd(value) {
  const absolute = formatUsd(Math.abs(value || 0));
  return `${value >= 0 ? "+" : "-"}${absolute.replace(/^\$/, "$")}`;
}

function formatSignedPercent(value) {
  return `${value >= 0 ? "+" : ""}${Number(value || 0).toFixed(2)}%`;
}

function buildNftImageUrl(tokenId) {
  if (!tokenId) {
    return "";
  }
  return `/v1/nfts/${tokenId}/image.svg`;
}

function normalizeStatus(status) {
  if (status === "COMPLETED") {
    return "Completed";
  }
  if (status === "RUNNING" || status === "QUEUED") {
    return "Pending";
  }
  return "Review";
}

function activityTone(status) {
  if (status === "Completed") {
    return "is-completed";
  }
  if (status === "Pending") {
    return "is-pending";
  }
  return "is-review";
}

function trendTone(value) {
  if (value > 0) {
    return "is-positive";
  }
  if (value < 0) {
    return "is-negative";
  }
  return "is-neutral";
}

async function handleWalletAction() {
  if (!store.state.metamask.address) {
    await store.connectMetaMask(true);
    return;
  }
  if (!store.authenticated.value) {
    await store.authenticateMetaMask({
      force: true,
      withRefresh: true,
    });
    return;
  }
  await store.refreshAll(true);
}
</script>
