<template>
  <div v-if="wallet" class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Wallet Link</span>
        <strong>{{ wallet.chain_address ? "Connected" : "Shadow Wallet" }}</strong>
        <p>{{ wallet.chain_address || "This runtime wallet has not been linked to an external chain address." }}</p>
      </article>
      <article class="metric-card">
        <span>Owned Agents</span>
        <strong>{{ ownedAgents.length }}</strong>
        <p>{{ ownedAgents.length ? "Agents currently controlled through this wallet's NFT ownership." : "No agents are currently owned by this wallet." }}</p>
      </article>
      <article class="metric-card">
        <span>Recent Requests</span>
        <strong>{{ walletRuns.length }}</strong>
        <p>{{ latestRun ? `Latest run status: ${latestRun.status}.` : "No run requests have been recorded for this wallet yet." }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Wallet</p>
          <h2>{{ wallet.name }}</h2>
        </div>
        <span class="panel-chip">{{ isSignedWallet ? "Signed Session" : wallet.balance }}</span>
      </header>
      <dl class="detail-list detail-list-two">
        <div>
          <dt>Wallet ID</dt>
          <dd>{{ wallet.id }}</dd>
        </div>
        <div>
          <dt>Chain Address</dt>
          <dd>{{ wallet.chain_address || "Unlinked" }}</dd>
        </div>
        <div>
          <dt>Local Balance</dt>
          <dd>{{ wallet.balance }}</dd>
        </div>
        <div>
          <dt>Runtime Session</dt>
          <dd>{{ isSignedWallet ? "Active" : "Inactive" }}</dd>
        </div>
      </dl>
      <div class="action-row">
        <button v-if="isSignedWallet" class="ghost-button" type="button" @click="router.push('/wallets/operator')">Operator View</button>
        <button v-if="wallet.chain_address" class="ghost-button" type="button" @click="copyChainAddress">Copy Address</button>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Ownership</p>
          <h2>Owned Agents</h2>
        </div>
        <span class="panel-chip">{{ ownedAgents.length }} agents</span>
      </header>
      <div v-if="!ownedAgents.length" class="empty-state">
        This wallet does not currently control any agent NFTs.
      </div>
      <div v-else class="stack-grid">
        <article v-for="agent in ownedAgents" :key="agent.id" class="entity-card">
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
              <dt>NFT</dt>
              <dd>{{ agent.nft.token_id }}</dd>
            </div>
          </dl>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="router.push(`/agents/${agent.id}`)">Agent Detail</button>
          </div>
        </article>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Market</p>
          <h2>Seller Activity</h2>
        </div>
        <span class="panel-chip">{{ walletListings.length }} listings</span>
      </header>
      <div v-if="!walletListings.length" class="empty-state">
        This wallet is not currently the seller on any open listing.
      </div>
      <div v-else class="stack-grid">
        <article v-for="listing in walletListings" :key="listing.id" class="entity-card">
          <div class="entity-card-header">
            <strong>{{ listing.id }}</strong>
            <span class="status-badge">{{ listing.price }}</span>
          </div>
          <dl class="detail-list">
            <div>
              <dt>Agent</dt>
              <dd>{{ listing.agent_id }}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{{ listing.status }}</dd>
            </div>
          </dl>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="router.push(`/market/listings/${listing.id}`)">Listing Detail</button>
          </div>
        </article>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Execution</p>
          <h2>Requested Runs</h2>
        </div>
        <span class="panel-chip">{{ walletRuns.length }} runs</span>
      </header>
      <div v-if="!walletRuns.length" class="empty-state">
        No run requests from this wallet have been recorded yet.
      </div>
      <div v-else class="stack-grid">
        <article v-for="run in walletRuns" :key="run.id" class="entity-card">
          <div class="entity-card-header">
            <strong>{{ run.id }}</strong>
            <span class="status-badge">{{ run.status }}</span>
          </div>
          <dl class="detail-list">
            <div>
              <dt>Agent</dt>
              <dd>{{ run.agent_id }}</dd>
            </div>
            <div>
              <dt>Started</dt>
              <dd>{{ store.formatDateTime(run.started_at) }}</dd>
            </div>
          </dl>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="router.push(`/runs/history/${run.id}`)">Run Detail</button>
          </div>
        </article>
      </div>
    </section>
  </div>

  <section v-else class="panel">
    <div class="empty-state">Wallet not found in the current runtime state.</div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();

const walletId = computed(() => String(route.params.walletId || ""));
const wallet = computed(() => store.resolveWalletById(walletId.value));
const isSignedWallet = computed(() => wallet.value?.id === store.state.metamask.wallet?.id && store.authenticated.value);
const ownedAgents = computed(() => store.state.agents.filter((agent) => agent.nft.owner_wallet_id === walletId.value));
const walletListings = computed(() => store.state.listings.filter((listing) => listing.seller_wallet_id === walletId.value));
const walletRuns = computed(() =>
  [...store.state.runs]
    .filter((run) => run.requested_by_wallet_id === walletId.value)
    .sort((left, right) => Date.parse(right.started_at || right.created_at || 0) - Date.parse(left.started_at || left.created_at || 0))
    .slice(0, 8)
);
const latestRun = computed(() => walletRuns.value[0] || null);

async function copyChainAddress() {
  if (!wallet.value?.chain_address) {
    return;
  }
  await store.copyText(wallet.value.chain_address);
  store.showFlash("Wallet address copied.", "success");
}
</script>
