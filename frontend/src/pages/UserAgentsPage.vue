<template>
  <div class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>Owned agents</span>
        <strong>{{ ownedAgents.length }}</strong>
        <p>Agents currently controlled by the signed wallet session.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Chain synced</span>
        <strong>{{ chainSyncedCount }}</strong>
        <p>Ownership enforced by chain state instead of local-only routing.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Listed</span>
        <strong>{{ listedAgentsCount }}</strong>
        <p>Portfolio assets currently offered through the market flow.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Run ready</span>
        <strong>{{ runReadyCount }}</strong>
        <p>Owned agents currently available for direct dispatch.</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Portfolio</p>
              <h2>Agent inventory</h2>
            </div>
            <div class="wallet-card-actions">
              <button class="wallet-home-primary" type="button" @click="router.push('/app/create')">New agent</button>
              <button class="wallet-home-secondary" type="button" @click="router.push('/app/market')">Open market</button>
            </div>
          </header>

          <p class="wallet-card-copy">
            Every row below represents an operator this wallet can actually control, trade, or dispatch.
          </p>

          <div class="wallet-home-table-shell">
            <div class="wallet-home-table-head wallet-agents-table">
              <div>Agent</div>
              <div>Mode</div>
              <div>Token</div>
              <div>Status</div>
              <div>Route</div>
            </div>

            <div
              v-for="agent in ownedAgents"
              :key="agent.id"
              class="wallet-home-table-row wallet-agents-table"
            >
              <div class="wallet-home-agent-cell">
                <div class="wallet-home-token-badge">{{ buildInitials(agent.name) }}</div>
                <div>
                  <strong>{{ agent.name }}</strong>
                  <span>{{ agent.id }}</span>
                </div>
              </div>
              <div>{{ store.formatSyncMode(agent.nft.sync_mode) }}</div>
              <div>{{ agent.nft.chain_token_id || agent.nft.token_id }}</div>
              <div>{{ agent.status }}</div>
              <div class="wallet-home-inline-meta">
                <span :class="{ positive: listedTokenIds.has(agent.nft.token_id) }">
                  {{ listedTokenIds.has(agent.nft.token_id) ? "Listed" : "Idle" }}
                </span>
                <RouterLink :to="`/app/agents/${agent.id}`">View</RouterLink>
              </div>
            </div>

            <div v-if="!ownedAgents.length" class="empty-state">
              You do not own any agents yet. Mint the first NFT-backed agent from the create flow to populate this portfolio.
            </div>
          </div>
        </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Portfolio routing</div>
          <div class="wallet-side-list">
            <div>
              <strong>Create path</strong>
              <span>Use the new agent flow to mint a fresh operator tied to this wallet session.</span>
            </div>
            <div>
              <strong>Dispatch path</strong>
              <span>Queue work from the runs lane once an owned agent is in a ready state.</span>
            </div>
            <div>
              <strong>Market route</strong>
              <span>List owned NFTs or acquire new ones through the market workspace.</span>
            </div>
            <div>
              <strong>Transfer route</strong>
              <span>Move direct control to another address from the transfer workspace.</span>
            </div>
          </div>
          <div class="wallet-side-actions-row">
            <button class="wallet-home-secondary" type="button" @click="router.push('/app/runs')">Runs</button>
            <button class="wallet-home-secondary" type="button" @click="router.push('/app/transfers')">Transfer</button>
          </div>
        </article>

        <article class="wallet-side-card">
          <div class="wallet-side-title">Recent portfolio agents</div>
          <div class="wallet-side-list">
            <div v-for="agent in ownedAgents.slice(0, 4)" :key="agent.id">
              <strong>{{ agent.name }}</strong>
              <span>{{ agent.nft.chain_token_id || agent.nft.token_id }} · {{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
            </div>
            <div v-if="!ownedAgents.length" class="wallet-side-empty">No owned agents yet.</div>
          </div>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const router = useRouter();
const store = useRuntimeStore();

const currentWalletId = computed(() => store.state.metamask.wallet?.id || null);
const ownedAgents = computed(() =>
  currentWalletId.value ? store.state.agents.filter((agent) => agent.nft.owner_wallet_id === currentWalletId.value) : []
);
const chainSyncedCount = computed(() => ownedAgents.value.filter((agent) => agent.nft.sync_mode === "CHAIN_SYNCED").length);
const listedTokenIds = computed(() => new Set(store.state.listings.map((listing) => listing.token_id)));
const listedAgentsCount = computed(() => ownedAgents.value.filter((agent) => listedTokenIds.value.has(agent.nft.token_id)).length);
const runReadyCount = computed(() => ownedAgents.value.filter((agent) => agent.status !== "DISABLED").length);

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
</script>
