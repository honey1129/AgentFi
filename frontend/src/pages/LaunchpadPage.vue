<template>
  <div class="page-grid page-grid-two">
    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Bootstrap</p>
          <h2>MetaMask Sign-In</h2>
        </div>
        <button class="ghost-button" type="button" @click="store.connectMetaMask(true)">Connect MetaMask</button>
      </header>
      <p class="panel-intro">
        Start the workspace by connecting MetaMask, binding the runtime wallet, and signing a session that will authorize creation, transfers, listings, and execution.
      </p>
      <div class="surface-block">
        <p class="surface-kicker">Operator Session</p>
        <h3 class="surface-title">Bind the active wallet to runtime access</h3>
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
      </div>
    </section>

    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Readiness</p>
          <h2>Session Overview</h2>
        </div>
        <span class="panel-chip">{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</span>
      </header>
      <p class="panel-intro">
        Review the current browser account, the mapped runtime wallet, and whether chain ownership sync is actually available before moving into agent creation.
      </p>
      <div class="surface-block stack-grid">
        <p class="surface-kicker">Readiness Check</p>
        <h3 class="surface-title">Current connection state</h3>
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
          <div>
            <dt>Chain Sync</dt>
            <dd>{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</dd>
          </div>
          <div>
            <dt>NFT Contract</dt>
            <dd>{{ store.state.runtime?.nft_contract_address || "Not configured" }}</dd>
          </div>
        </dl>

        <div class="empty-state">
          Connect MetaMask first, then sign the challenge so the backend can bind your runtime wallet to the active address.
          After that, move to <strong>Create Agent</strong> to mint a new ownership NFT.
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
