<template>
  <section class="panel">
    <header class="panel-header">
      <div>
        <p class="section-label">Ownership</p>
        <h2>Agents &amp; Ownership</h2>
      </div>
      <span class="panel-chip">{{ store.state.agents.length }} agents</span>
    </header>
    <p class="panel-intro">
      Browse the current fleet with owner, token, sync mode, and prompt context in one scan. Use the card actions to move directly into execution, schedules, or market operations.
    </p>
    <div v-if="!store.state.agents.length" class="empty-state">
      No agents yet. Create one from the launchpad to mint its ownership NFT.
    </div>
    <div v-else class="entity-grid">
      <article
        v-for="agent in store.state.agents"
        :key="agent.id"
        class="entity-card"
      >
        <div class="entity-card-header">
          <strong>{{ agent.name }}</strong>
          <span class="status-badge">{{ agent.status }}</span>
        </div>
        <dl class="detail-list">
          <div>
            <dt>Agent ID</dt>
            <dd>{{ agent.id }}</dd>
          </div>
          <div>
            <dt>Owner Wallet</dt>
            <dd>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</dd>
          </div>
          <div>
            <dt>Ownership Mode</dt>
            <dd>{{ store.formatSyncMode(agent.nft.sync_mode) }}</dd>
          </div>
          <div>
            <dt>NFT</dt>
            <dd>{{ agent.nft.token_id }}</dd>
          </div>
          <div>
            <dt>Chain Token</dt>
            <dd>{{ agent.nft.chain_token_id || "Off-chain only" }}</dd>
          </div>
          <div>
            <dt>Prompt</dt>
            <dd>{{ store.truncate(agent.system_prompt, 160) }}</dd>
          </div>
        </dl>
        <div class="action-row">
          <button class="ghost-button" type="button" @click="router.push(`/agents/${agent.id}`)">Details</button>
          <button class="ghost-button" type="button" @click="router.push({ path: '/runs/queue', query: { agent_id: agent.id } })">Queue Run</button>
          <button class="ghost-button" type="button" @click="router.push({ path: '/runs/schedules', query: { agent_id: agent.id } })">Schedule</button>
          <button class="ghost-button" type="button" @click="router.push({ path: '/market/listings', query: { token_id: agent.nft.token_id } })">List</button>
          <button class="ghost-button" type="button" @click="router.push({ path: '/market/transfers', query: { token_id: agent.nft.token_id } })">Transfer</button>
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
