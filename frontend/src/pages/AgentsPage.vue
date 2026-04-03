<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Agents</span>
        <strong>{{ store.state.agents.length }}</strong>
        <p>Total agent records currently registered.</p>
      </article>
      <article class="metric-card">
        <span>Chain Synced</span>
        <strong>{{ syncedAgentsCount }}</strong>
        <p>Agents whose ownership follows on-chain NFT state.</p>
      </article>
      <article class="metric-card">
        <span>Listed</span>
        <strong>{{ listedAgentsCount }}</strong>
        <p>Agents whose NFTs are currently in the market inventory.</p>
      </article>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Directory</p>
          <h2>Agent Registry</h2>
        </div>
        <span class="panel-chip">{{ store.state.agents.length }} records</span>
      </header>
      <p class="panel-intro">
        Use this page as the operational registry for ownership, sync mode, and prompt state. Deep inspection lives in the detail page, but the primary queue, market, and transfer actions stay one click away.
      </p>
      <div v-if="!store.state.agents.length" class="empty-state">
        No agents yet. Create one from the launchpad to mint its ownership NFT.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head agents-table">
          <span>Agent</span>
          <span>Owner</span>
          <span>Mode</span>
          <span>Token</span>
          <span>Prompt</span>
          <span>Actions</span>
        </div>
        <article
          v-for="agent in store.state.agents"
          :key="agent.id"
          class="data-table-row agents-table"
        >
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ agent.name }}</strong>
              <span class="text-muted">{{ agent.id }}</span>
            </div>
          </div>
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</strong>
              <span class="text-muted">{{ agent.status }}</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="status-badge">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
          </div>
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ agent.nft.token_id }}</strong>
              <span class="text-muted">{{ agent.nft.chain_token_id || "Off-chain only" }}</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ store.truncate(agent.system_prompt, 120) }}</span>
          </div>
          <div class="table-cell">
            <div class="table-actions">
              <button class="ghost-button" type="button" @click="router.push(`/agents/${agent.id}`)">Detail</button>
              <button class="ghost-button" type="button" @click="router.push({ path: '/runs/queue', query: { agent_id: agent.id } })">Run</button>
              <button class="ghost-button" type="button" @click="router.push({ path: '/market/listings', query: { token_id: agent.nft.token_id } })">List</button>
              <button class="ghost-button" type="button" @click="router.push({ path: '/market/transfers', query: { token_id: agent.nft.token_id } })">Transfer</button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const router = useRouter();
const store = useRuntimeStore();
const syncedAgentsCount = computed(() =>
  store.state.agents.filter((agent) => agent.nft.sync_mode === "CHAIN_SYNCED").length
);
const listedAgentsCount = computed(() => {
  const listedTokenIds = new Set(store.state.listings.map((listing) => listing.token_id));
  return store.state.agents.filter((agent) => listedTokenIds.has(agent.nft.token_id)).length;
});
</script>
