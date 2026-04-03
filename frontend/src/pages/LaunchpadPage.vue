<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Session</span>
        <strong>{{ store.authenticated.value ? "Signed" : "Unsigned" }}</strong>
        <p>{{ store.authenticated.value ? "Current browser wallet can submit protected writes." : "Sign a challenge before creating, listing, or transferring." }}</p>
      </article>
      <article class="metric-card">
        <span>Address</span>
        <strong>{{ store.state.metamask.address ? store.truncate(store.state.metamask.address, 16) : "Not connected" }}</strong>
        <p>{{ store.state.metamask.chainId ? `Chain ${store.state.metamask.chainId}` : "No wallet connected in this browser." }}</p>
      </article>
      <article class="metric-card">
        <span>Chain Sync</span>
        <strong>{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</strong>
        <p>{{ store.state.runtime?.nft_contract_address || "NFT contract not configured for this runtime." }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Authenticate</p>
          <h2>MetaMask Sign-In</h2>
        </div>
        <button class="ghost-button" type="button" @click="store.connectMetaMask(true)">Connect MetaMask</button>
      </header>
      <form class="form-grid" @submit.prevent="submitWallet">
        <label class="field">
          <span>Wallet Label</span>
          <input v-model="walletForm.label" placeholder="main_operator" />
        </label>
        <label class="field">
          <span>Bootstrap Balance</span>
          <input v-model="walletForm.initialBalance" type="number" min="0" step="0.01" />
        </label>
        <label class="field field-full">
          <span>Connected Address</span>
          <input :value="store.state.metamask.address || ''" placeholder="0x..." readonly />
        </label>
        <div class="action-row field-full">
          <button class="ghost-button" type="button" @click="store.connectMetaMask(true)">Connect</button>
          <button class="primary-button" type="submit">Sign In &amp; Sync</button>
          <button class="ghost-button" type="button" @click="store.logoutMetaMask(true)">Logout</button>
        </div>
      </form>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Readiness</p>
          <h2>Operator Readiness</h2>
        </div>
        <span class="panel-chip">{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</span>
      </header>
      <div class="stack-grid">
        <div class="surface-block">
          <p class="surface-kicker">Connection</p>
          <h3 class="surface-title">Browser wallet</h3>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>MetaMask Address</dt>
              <dd>{{ store.state.metamask.address || "Not connected" }}</dd>
            </div>
            <div>
              <dt>Chain ID</dt>
              <dd>{{ store.state.metamask.chainId || "Unavailable" }}</dd>
            </div>
            <div>
              <dt>Runtime Session</dt>
              <dd>{{ store.authenticated.value ? "Signed" : "Unsigned" }}</dd>
            </div>
            <div>
              <dt>Runtime Wallet</dt>
              <dd>{{ store.state.metamask.wallet?.name || store.state.metamask.wallet?.id || "Not mapped yet" }}</dd>
            </div>
          </dl>
        </div>
        <div class="surface-block">
          <p class="surface-kicker">Chain Setup</p>
          <h3 class="surface-title">Runtime configuration</h3>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Chain Sync</dt>
              <dd>{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</dd>
            </div>
            <div>
              <dt>NFT Contract</dt>
              <dd>{{ store.state.runtime?.nft_contract_address || "Not configured" }}</dd>
            </div>
            <div>
              <dt>Marketplace</dt>
              <dd>{{ store.state.runtime?.marketplace_contract_address || "Not configured" }}</dd>
            </div>
            <div>
              <dt>Auto Mint</dt>
              <dd>{{ store.state.runtime?.auto_onchain_mint_enabled ? "Enabled" : "Disabled" }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive } from "vue";

import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();

const walletForm = reactive({
  label: "",
  initialBalance: "1000",
});

async function submitWallet() {
  await store.authenticateMetaMask({
    force: true,
    initialBalance: walletForm.initialBalance || "0",
    label: walletForm.label || null,
    withRefresh: true,
  });
}
</script>
