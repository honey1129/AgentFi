<template>
  <div class="page-grid page-grid-two">
    <section class="panel">
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

    <section class="panel">
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
      <div v-else class="entity-grid">
        <article v-for="agent in store.state.agents" :key="agent.id" class="entity-card">
          <div class="entity-card-header">
            <strong>{{ agent.name }}</strong>
            <span class="status-badge">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
          </div>
          <dl class="detail-list">
            <div>
              <dt>NFT</dt>
              <dd>{{ agent.nft.token_id }}</dd>
            </div>
            <div>
              <dt>Owner</dt>
              <dd>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Contract</dt>
              <dd>{{ agent.nft.contract_address || "Local only" }}</dd>
            </div>
          </dl>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="prefillTransfer(agent.nft.token_id)">Use in Form</button>
            <button class="ghost-button" type="button" @click="router.push(`/agents/${agent.id}`)">Agent Detail</button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();

const transferForm = reactive({
  token_id: "",
  to_chain_address: "",
});

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
