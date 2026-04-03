<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Agents</span>
        <strong>{{ store.state.agents.length }}</strong>
        <p>Total agents currently provisioned in this runtime.</p>
      </article>
      <article class="metric-card">
        <span>Auto Mint</span>
        <strong>{{ store.state.runtime?.auto_onchain_mint_enabled ? "Enabled" : "Disabled" }}</strong>
        <p>{{ store.state.runtime?.nft_contract_address || "No NFT contract configured." }}</p>
      </article>
      <article class="metric-card">
        <span>Owner</span>
        <strong>{{ store.authenticated.value ? (store.state.metamask.wallet?.name || "Signed session") : "Unsigned" }}</strong>
        <p>New agents always bind ownership to the current signed MetaMask session.</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Create</p>
          <h2>Create Agent + NFT</h2>
        </div>
        <span class="panel-chip">On-chain mint if configured</span>
      </header>
      <form class="form-grid" @submit.prevent="submitAgent">
        <label class="field">
          <span>Name</span>
          <input v-model="agentForm.name" placeholder="Research Agent" required />
        </label>
        <label class="field">
          <span>NFT Contract</span>
          <input v-model="agentForm.contract_address" placeholder="0x..." />
        </label>
        <label class="field field-full">
          <span>Description</span>
          <textarea v-model="agentForm.description" rows="3" placeholder="Tracks alpha and drafts operator notes" required />
        </label>
        <label class="field field-full">
          <span>System Prompt</span>
          <textarea v-model="agentForm.system_prompt" rows="5" placeholder="Act like a disciplined crypto operator..." required />
        </label>
        <label class="field">
          <span>Chain Token ID</span>
          <input v-model="agentForm.chain_token_id" placeholder="42" />
        </label>
        <div class="field field-full">
          <p class="field-note">Owner wallet is always the currently signed MetaMask session.</p>
        </div>
        <div class="action-row field-full">
          <button class="primary-button" type="submit">Spawn Agent</button>
        </div>
      </form>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Recent</p>
          <h2>Latest Agents</h2>
        </div>
        <span class="panel-chip">{{ store.state.agents.length }} total</span>
      </header>
      <div v-if="!store.state.agents.length" class="empty-state">
        No agents yet. Sign a session first, then mint the first ownership NFT from this page.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head compact-history-table">
          <span>Agent</span>
          <span>Owner</span>
          <span>Token</span>
          <span>Mode</span>
          <span>Actions</span>
          <span>Status</span>
        </div>
        <article v-for="agent in recentAgents" :key="agent.id" class="data-table-row compact-history-table">
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ agent.name }}</strong>
              <span class="text-muted">{{ agent.id }}</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ store.describeWallet(agent.nft.owner_wallet_id) }}</span>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ agent.nft.token_id }}</span>
          </div>
          <div class="table-cell">
            <span class="status-badge">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
          </div>
          <div class="table-cell">
            <div class="table-actions">
              <button class="ghost-button" type="button" @click="router.push(`/agents/${agent.id}`)">Detail</button>
            </div>
          </div>
          <div class="table-cell">
            <span class="status-badge">{{ agent.status }}</span>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";
import { useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();
const router = useRouter();

const agentForm = reactive({
  name: "",
  description: "",
  system_prompt: "",
  contract_address: "",
  chain_token_id: "",
});

const recentAgents = computed(() => [...store.state.agents].slice(0, 4));

async function submitAgent() {
  await store.createAgent({
    ...agentForm,
    contract_address: agentForm.contract_address || null,
    chain_token_id: agentForm.chain_token_id || null,
  });
  agentForm.name = "";
  agentForm.description = "";
  agentForm.system_prompt = "";
  agentForm.contract_address = "";
  agentForm.chain_token_id = "";
}
</script>
