<template>
  <div class="page-grid page-grid-two">
    <section class="panel">
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

    <section class="panel">
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
      <div v-else class="stack-grid">
        <article v-for="agent in recentAgents" :key="agent.id" class="entity-card">
          <div class="entity-card-header">
            <strong>{{ agent.name }}</strong>
            <span class="status-badge">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
          </div>
          <dl class="detail-list">
            <div>
              <dt>Agent ID</dt>
              <dd>{{ agent.id }}</dd>
            </div>
            <div>
              <dt>NFT Token</dt>
              <dd>{{ agent.nft.token_id }}</dd>
            </div>
            <div>
              <dt>Owner</dt>
              <dd>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</dd>
            </div>
          </dl>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";

import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();

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
