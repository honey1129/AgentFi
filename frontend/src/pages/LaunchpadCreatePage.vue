<template>
  <div v-if="isUserView" class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>Portfolio agents</span>
        <strong>{{ recentAgents.length }}</strong>
        <p>Agents already owned by the current wallet.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Auto mint</span>
        <strong>{{ store.state.runtime?.auto_onchain_mint_enabled ? "Enabled" : "Disabled" }}</strong>
        <p>{{ store.state.runtime?.nft_contract_address || "No NFT contract configured." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Session owner</span>
        <strong>{{ store.authenticated.value ? (store.state.metamask.wallet?.name || "Signed session") : "Unsigned" }}</strong>
        <p>New agents always bind ownership to the current signed MetaMask session.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Mint path</span>
        <strong>{{ store.state.runtime?.marketplace_contract_address ? "Market ready" : "Runtime only" }}</strong>
        <p>{{ store.state.runtime?.marketplace_contract_address || "Marketplace contract not configured." }}</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
      <article class="wallet-card">
        <header class="wallet-card-header">
          <div>
            <p class="wallet-card-kicker">Create</p>
            <h2>New agent</h2>
          </div>
          <span class="wallet-status-pill is-completed">Wallet owned</span>
        </header>

        <form class="wallet-form-grid" @submit.prevent="submitAgent">
          <label class="wallet-field">
            <span>Name</span>
            <input v-model="agentForm.name" placeholder="Research Agent" required />
          </label>
          <label class="wallet-field">
            <span>NFT contract</span>
            <input v-model="agentForm.contract_address" placeholder="0x..." />
          </label>
          <label class="wallet-field wallet-field-full">
            <span>Description</span>
            <textarea v-model="agentForm.description" rows="3" placeholder="Tracks alpha and drafts operator notes" required />
          </label>
          <label class="wallet-field wallet-field-full">
            <span>System prompt</span>
            <textarea v-model="agentForm.system_prompt" rows="5" placeholder="Act like a disciplined crypto operator..." required />
          </label>
          <label class="wallet-field">
            <span>Chain token ID</span>
            <input v-model="agentForm.chain_token_id" placeholder="42" />
          </label>
          <div class="wallet-form-note wallet-field-full">
            Ownership always binds to the current signed wallet session. If runtime auto mint is enabled, the ownership NFT is created as part of this flow.
          </div>
          <div class="wallet-form-actions wallet-field-full">
            <button class="wallet-home-primary" type="submit">Create agent</button>
          </div>
        </form>
      </article>

      <article class="wallet-card">
        <header class="wallet-card-header">
          <div>
            <p class="wallet-card-kicker">Recent</p>
            <h2>Latest portfolio agents</h2>
          </div>
          <span class="wallet-status-pill">{{ recentAgents.length }} recent</span>
        </header>

        <div v-if="!recentAgents.length" class="empty-state">
          No agents yet. Sign a session first, then mint the first ownership NFT from this page.
        </div>
        <div v-else class="wallet-side-list">
          <div v-for="agent in recentAgents" :key="agent.id">
            <strong>{{ agent.name }}</strong>
            <span>{{ agent.id }} · {{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
          </div>
        </div>
      </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Create notes</div>
          <div class="wallet-side-list">
            <div>
              <strong>Wallet bound</strong>
              <span>Ownership always binds to the current signed wallet session.</span>
            </div>
            <div>
              <strong>Auto mint</strong>
              <span>{{ store.state.runtime?.auto_onchain_mint_enabled ? "NFT mint route is enabled for this runtime." : "Mint route is disabled in this environment." }}</span>
            </div>
            <div>
              <strong>Marketplace</strong>
              <span>{{ store.state.runtime?.marketplace_contract_address || "No marketplace contract configured." }}</span>
            </div>
          </div>
        </article>
      </aside>
    </section>
  </div>

  <div v-else class="page-grid">
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
              <button class="ghost-button" type="button" @click="openAgentDetail(agent.id)">Detail</button>
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
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();
const router = useRouter();
const route = useRoute();
const isUserView = computed(() => route.meta.audience === "user");
const currentWalletId = computed(() => store.state.metamask.wallet?.id || null);

const agentForm = reactive({
  name: "",
  description: "",
  system_prompt: "",
  contract_address: "",
  chain_token_id: "",
});

const recentAgents = computed(() => {
  const source = isUserView.value && currentWalletId.value
    ? store.state.agents.filter((agent) => agent.nft.owner_wallet_id === currentWalletId.value)
    : store.state.agents;
  return [...source].slice(0, 4);
});

function openAgentDetail(agentId) {
  router.push(`${isUserView.value ? "/app" : ""}/agents/${agentId}`);
}

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
