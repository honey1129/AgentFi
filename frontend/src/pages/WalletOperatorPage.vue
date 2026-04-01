<template>
  <div class="page-grid page-grid-two">
    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Operator</p>
          <h2>Current Session</h2>
        </div>
        <span class="panel-chip">{{ store.authenticated.value ? "SIGNED" : "UNSIGNED" }}</span>
      </header>
      <p class="panel-intro">
        Review the exact browser wallet that is connected right now and whether the runtime has accepted a signed session for it.
      </p>
      <div class="surface-block">
        <p class="surface-kicker">Session Status</p>
        <h3 class="surface-title">Connected browser identity</h3>
        <dl class="detail-list detail-list-two">
          <div>
            <dt>MetaMask Available</dt>
            <dd>{{ String(store.state.metamask.available) }}</dd>
          </div>
          <div>
            <dt>Connected Address</dt>
            <dd>{{ store.state.metamask.address || "Not connected" }}</dd>
          </div>
          <div>
            <dt>Chain ID</dt>
            <dd>{{ store.state.metamask.chainId || "Unavailable" }}</dd>
          </div>
          <div>
            <dt>Runtime Session</dt>
            <dd>{{ store.authenticated.value ? "Authenticated" : "Needs signature" }}</dd>
          </div>
        </dl>
      </div>
      <div class="action-row">
        <button class="ghost-button" type="button" @click="store.connectMetaMask(true)">Connect MetaMask</button>
        <button class="primary-button" type="button" @click="signIn">Sign In &amp; Sync</button>
        <button class="ghost-button" type="button" @click="store.logoutMetaMask(true)">Logout</button>
      </div>
    </section>

    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Runtime Wallet</p>
          <h2>Mapped Identity</h2>
        </div>
        <span class="panel-chip">{{ store.state.metamask.wallet?.id || "No wallet" }}</span>
      </header>
      <p class="panel-intro">
        Once the session is signed, the runtime wallet below becomes the identity that owns, trades, and dispatches agents on behalf of the current browser account.
      </p>
      <div v-if="store.state.metamask.wallet" class="stack-grid">
        <div class="surface-block">
          <p class="surface-kicker">Runtime Mapping</p>
          <h3 class="surface-title">Wallet bound to this operator</h3>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Wallet ID</dt>
              <dd>{{ store.state.metamask.wallet.id }}</dd>
            </div>
            <div>
              <dt>Wallet Label</dt>
              <dd>{{ store.state.metamask.wallet.name }}</dd>
            </div>
            <div>
              <dt>Chain Address</dt>
              <dd>{{ store.state.metamask.wallet.chain_address || "Unlinked" }}</dd>
            </div>
            <div>
              <dt>Balance</dt>
              <dd>{{ store.state.metamask.wallet.balance }}</dd>
            </div>
          </dl>
        </div>
      </div>
      <div v-else class="empty-state">
        No runtime wallet is bound to the current address yet. Sign the challenge to create or recover the mapped wallet.
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();

async function signIn() {
  await store.authenticateMetaMask({
    force: true,
    withRefresh: true,
  });
}
</script>
