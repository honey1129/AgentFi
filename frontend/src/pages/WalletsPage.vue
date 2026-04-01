<template>
  <section class="panel">
    <header class="panel-header">
      <div>
        <p class="section-label">Registry</p>
        <h2>Wallet Registry</h2>
      </div>
      <span class="panel-chip">{{ store.state.wallets.length }} wallets</span>
    </header>
    <p class="panel-intro">
      A quiet registry for runtime identities, linked chain addresses, and local balances. Use it as the canonical reference before you move into ownership, trading, or execution.
    </p>
    <div v-if="!store.state.wallets.length" class="empty-state">
      No wallets yet. Connect MetaMask from the launchpad to create the first runtime wallet.
    </div>
    <div v-else class="entity-grid">
      <article
        v-for="wallet in store.state.wallets"
        :key="wallet.id"
        class="entity-card"
      >
        <div class="entity-card-header">
          <strong>{{ wallet.name }}</strong>
          <span class="status-badge">
            {{ wallet.id === store.state.metamask.wallet?.id && store.authenticated.value ? "Signed Session" : wallet.balance }}
          </span>
        </div>
        <dl class="detail-list">
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
        </dl>
        <div class="action-row">
          <button class="ghost-button" type="button" @click="router.push(`/wallets/${wallet.id}`)">Detail</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const router = useRouter();
const store = useRuntimeStore();
</script>
