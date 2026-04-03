<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Transferable NFTs</span>
        <strong>{{ store.state.agents.length }}</strong>
        <p>NFT-backed agents currently available for direct handoff.</p>
      </article>
      <article class="metric-card">
        <span>Chain Synced</span>
        <strong>{{ chainSyncedCount }}</strong>
        <p>Transfers that will prefer a real on-chain MetaMask flow.</p>
      </article>
      <article class="metric-card">
        <span>Selected NFT</span>
        <strong>{{ transferForm.token_id || "None" }}</strong>
        <p>{{ transferForm.to_chain_address || "Pick a token and destination address to prepare transfer." }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Actions</p>
          <h2>Transfer Ownership</h2>
        </div>
        <span class="panel-chip">Direct handoff</span>
      </header>
      <form class="form-grid compact-grid" @submit.prevent="submitTransfer">
        <label class="field field-full">
          <span>NFT</span>
          <select v-model="transferForm.token_id" required>
            <option disabled value="">Select an NFT</option>
            <option v-for="agent in store.state.agents" :key="agent.nft.token_id" :value="agent.nft.token_id">
              {{ agent.name }} · {{ agent.nft.token_id }}
            </option>
          </select>
        </label>
        <label class="field field-full">
          <span>To Chain Address</span>
          <input v-model="transferForm.to_chain_address" placeholder="0x..." required />
        </label>
        <div class="field field-full">
          <p class="field-note">
            If this NFT is chain-synced, the runtime will prefer a MetaMask on-chain transfer. Otherwise it falls back to the local transfer flow.
          </p>
        </div>
        <div class="action-row field-full">
          <button class="primary-button" type="submit">Transfer NFT</button>
        </div>
      </form>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Inventory</p>
          <h2>Ownership Inventory</h2>
        </div>
        <span class="panel-chip">{{ store.state.agents.length }} agents</span>
      </header>
      <div v-if="!store.state.agents.length" class="empty-state">
        No NFT-backed agents exist yet.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head transfer-table">
          <span>Agent</span>
          <span>Token</span>
          <span>Owner</span>
          <span>Mode</span>
          <span>Contract</span>
          <span>Actions</span>
        </div>
        <article v-for="agent in store.state.agents" :key="agent.id" class="data-table-row transfer-table">
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ agent.name }}</strong>
              <span class="text-muted">{{ agent.id }}</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ agent.nft.token_id }}</span>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ store.describeWallet(agent.nft.owner_wallet_id) }}</span>
          </div>
          <div class="table-cell">
            <span class="status-badge">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ agent.nft.contract_address || "Local only" }}</span>
          </div>
          <div class="table-cell">
            <div class="table-actions">
              <button class="ghost-button" type="button" @click="prefillTransfer(agent.nft.token_id)">Use in Form</button>
              <button class="ghost-button" type="button" @click="router.push(`/agents/${agent.id}`)">Agent Detail</button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();

const transferForm = reactive({
  token_id: "",
  to_chain_address: "",
});
const chainSyncedCount = computed(() =>
  store.state.agents.filter((agent) => agent.nft.sync_mode === "CHAIN_SYNCED").length
);

watch(
  () => route.query,
  (query) => {
    if (typeof query.token_id === "string") {
      transferForm.token_id = query.token_id;
    }
  },
  { immediate: true }
);

async function submitTransfer() {
  await store.transferNft(transferForm.token_id, transferForm.to_chain_address);
  transferForm.to_chain_address = "";
}

function prefillTransfer(tokenId) {
  transferForm.token_id = tokenId;
}
</script>
