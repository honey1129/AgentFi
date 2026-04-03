<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Wallets</span>
        <strong>{{ store.state.wallets.length }}</strong>
        <p>Runtime identities known to the backend.</p>
      </article>
      <article class="metric-card">
        <span>Linked</span>
        <strong>{{ linkedWalletsCount }}</strong>
        <p>Wallets already mapped to a chain address.</p>
      </article>
      <article class="metric-card">
        <span>Signed</span>
        <strong>{{ store.authenticated.value ? 1 : 0 }}</strong>
        <p>Active browser session currently authenticated.</p>
      </article>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Registry</p>
          <h2>Wallet Registry</h2>
        </div>
        <span class="panel-chip">{{ store.state.wallets.length }} wallets</span>
      </header>
      <p class="panel-intro">
        Use the wallet registry as the canonical source for runtime identities, linked chain addresses, and balances before moving into ownership or execution.
      </p>
      <div v-if="!store.state.wallets.length" class="empty-state">
        No wallets yet. Connect MetaMask from the launchpad to create the first runtime wallet.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head wallet-table">
          <span>Wallet</span>
          <span>Chain Address</span>
          <span>Balance</span>
          <span>State</span>
          <span>Actions</span>
        </div>
        <article v-for="wallet in store.state.wallets" :key="wallet.id" class="data-table-row wallet-table">
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ wallet.name }}</strong>
              <span class="text-muted">{{ wallet.id }}</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ wallet.chain_address || "Unlinked" }}</span>
          </div>
          <div class="table-cell">
            <strong>{{ wallet.balance }}</strong>
          </div>
          <div class="table-cell">
            <span class="status-badge">
              {{ wallet.id === store.state.metamask.wallet?.id && store.authenticated.value ? "Signed Session" : "Registry Wallet" }}
            </span>
          </div>
          <div class="table-cell">
            <div class="table-actions">
              <button class="ghost-button" type="button" @click="router.push(`/wallets/${wallet.id}`)">Detail</button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const router = useRouter();
const store = useRuntimeStore();
const linkedWalletsCount = computed(() => store.state.wallets.filter((wallet) => wallet.chain_address).length);
</script>
