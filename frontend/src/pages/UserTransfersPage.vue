<template>
  <div class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>Owned NFTs</span>
        <strong>{{ ownedAgents.length }}</strong>
        <p>NFT-backed agents controlled by the current wallet.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Chain synced</span>
        <strong>{{ chainSyncedCount }}</strong>
        <p>Transfers that will execute directly on-chain via MetaMask.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Selected NFT</span>
        <strong>{{ transferForm.token_id || "None" }}</strong>
        <p>{{ selectedAgent ? selectedAgent.name : "Select a portfolio asset to transfer." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Destination</span>
        <strong>{{ transferForm.to_chain_address ? store.truncate(transferForm.to_chain_address, 18) : "Not set" }}</strong>
        <p>{{ selectedAgent && store.shouldUseOnChainTransfer(selectedAgent.nft) ? "Will request MetaMask transfer." : "Runtime transfer path if local-only." }}</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Inventory</p>
              <h2>Transferable portfolio</h2>
            </div>
            <span class="wallet-status-pill">{{ ownedAgents.length }} owned</span>
          </header>

          <p class="wallet-card-copy">
            Start from the owned inventory first, then prefill an NFT into the direct handoff form when you are ready to transfer control.
          </p>

          <div class="wallet-home-table-shell">
            <div class="wallet-home-table-head wallet-transfer-table">
              <div>Agent</div>
              <div>Sync mode</div>
              <div>Token</div>
              <div>Route</div>
              <div>Actions</div>
            </div>

            <div
              v-for="agent in ownedAgents"
              :key="agent.id"
              class="wallet-home-table-row wallet-transfer-table"
            >
              <div class="wallet-home-agent-cell">
                <div class="wallet-home-token-badge">{{ buildInitials(agent.name) }}</div>
                <div>
                  <strong>{{ agent.name }}</strong>
                  <span>{{ agent.id }}</span>
                </div>
              </div>
              <div>{{ store.formatSyncMode(agent.nft.sync_mode) }}</div>
              <div>{{ agent.nft.token_id }}</div>
              <div>{{ store.shouldUseOnChainTransfer(agent.nft) ? "On-chain" : "Runtime" }}</div>
              <div class="wallet-home-inline-meta">
                <button class="wallet-table-button" type="button" @click="prefillTransfer(agent.nft.token_id)">Use</button>
                <RouterLink :to="`/app/agents/${agent.id}`">Detail</RouterLink>
              </div>
            </div>

            <div v-if="!ownedAgents.length" class="empty-state">
              No transferable NFTs are currently controlled by this wallet.
            </div>
          </div>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Transfer</p>
              <h2>Direct ownership handoff</h2>
            </div>
            <span class="wallet-status-pill is-pending">{{ selectedAgent && store.shouldUseOnChainTransfer(selectedAgent.nft) ? "On-chain" : "Runtime" }}</span>
          </header>

          <p class="wallet-card-copy">
            Chain-synced NFTs open a MetaMask transfer. Local-only NFTs stay in the runtime handoff path.
          </p>

          <form class="wallet-form-grid" @submit.prevent="submitTransfer">
            <label class="wallet-field wallet-field-full">
              <span>Owned NFT</span>
              <select v-model="transferForm.token_id" required>
                <option disabled value="">Select one of your NFTs</option>
                <option v-for="agent in ownedAgents" :key="agent.nft.token_id" :value="agent.nft.token_id">
                  {{ agent.name }} · {{ agent.nft.token_id }}
                </option>
              </select>
            </label>
            <label class="wallet-field wallet-field-full">
              <span>Destination address</span>
              <input v-model="transferForm.to_chain_address" placeholder="0x..." required />
            </label>
            <div class="wallet-form-note wallet-field-full">
              Transfers route according to the NFT sync mode configured on the selected asset.
            </div>
            <div class="wallet-form-actions wallet-field-full">
              <button class="wallet-home-primary" type="submit">Transfer NFT</button>
            </div>
          </form>

          <div v-if="selectedAgent" class="wallet-inline-card">
            <span>Transfer path</span>
            <strong>{{ selectedAgent.name }}</strong>
            <p>{{ selectedAgent.nft.contract_address || "No contract mapping" }} · {{ store.formatSyncMode(selectedAgent.nft.sync_mode) }}</p>
          </div>
        </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Transfer routing</div>
          <div class="wallet-side-list">
            <div>
              <strong>Route</strong>
              <span>{{ selectedAgent && store.shouldUseOnChainTransfer(selectedAgent.nft) ? "MetaMask transfer flow" : "Runtime ownership handoff" }}</span>
            </div>
            <div>
              <strong>Current wallet</strong>
              <span>{{ store.state.metamask.wallet?.name || "Not mapped" }}</span>
            </div>
            <div>
              <strong>Chain sync</strong>
              <span>{{ chainSyncedCount }} NFTs currently chain-synced.</span>
            </div>
          </div>
        </article>

        <article class="wallet-side-card">
          <div class="wallet-side-title">Current selection</div>
          <div class="wallet-side-list">
            <div>
              <strong>Selected NFT</strong>
              <span>{{ selectedAgent ? `${selectedAgent.name} · ${selectedAgent.nft.token_id}` : "Nothing selected yet." }}</span>
            </div>
            <div>
              <strong>Destination</strong>
              <span>{{ transferForm.to_chain_address || "No destination address entered." }}</span>
            </div>
            <div>
              <strong>Status</strong>
              <span>{{ selectedAgent ? store.formatSyncMode(selectedAgent.nft.sync_mode) : "Awaiting selection" }}</span>
            </div>
          </div>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { useRoute } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const store = useRuntimeStore();

const transferForm = reactive({
  token_id: "",
  to_chain_address: "",
});

const currentWalletId = computed(() => store.state.metamask.wallet?.id || null);
const ownedAgents = computed(() =>
  currentWalletId.value ? store.state.agents.filter((agent) => agent.nft.owner_wallet_id === currentWalletId.value) : []
);
const chainSyncedCount = computed(() => ownedAgents.value.filter((agent) => agent.nft.sync_mode === "CHAIN_SYNCED").length);
const selectedAgent = computed(() => ownedAgents.value.find((agent) => agent.nft.token_id === transferForm.token_id) || null);

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
