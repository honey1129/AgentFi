<template>
  <div v-if="resolvedListing && agent" class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Ask Price</span>
        <strong>{{ resolvedListing.price }}</strong>
        <p>The sale listing currently exposes ownership transfer for token {{ resolvedListing.token_id }}.</p>
      </article>
      <article class="metric-card">
        <span>Holder Check</span>
        <strong>{{ holderState }}</strong>
        <p>{{ resolvedListing.seller_wallet_id === agent.nft.owner_wallet_id ? "Seller and current holder still match." : "Seller and current holder have diverged. Review ownership before buying." }}</p>
      </article>
      <article class="metric-card">
        <span>Settlement Mode</span>
        <strong>{{ resolvedListing.market_mode }}</strong>
        <p>{{ agent.nft.contract_address ? `Contract ${agent.nft.contract_address}` : "No on-chain contract is linked to this token yet." }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Listing</p>
          <h2>{{ resolvedListing.id }}</h2>
        </div>
        <span class="panel-chip">{{ resolvedListing.status }}</span>
      </header>
      <div class="spotlight-media">
        <img :src="store.getTokenImageUrl(resolvedListing.token_id)" :alt="agent.name" />
      </div>
      <dl class="detail-list detail-list-two">
        <div>
          <dt>Price</dt>
          <dd>{{ resolvedListing.price }}</dd>
        </div>
        <div>
          <dt>NFT Token</dt>
          <dd>{{ resolvedListing.token_id }}</dd>
        </div>
        <div>
          <dt>Seller</dt>
          <dd>{{ store.describeWallet(resolvedListing.seller_wallet_id) }}</dd>
        </div>
        <div>
          <dt>Holder</dt>
          <dd>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</dd>
        </div>
        <div>
          <dt>Sync Mode</dt>
          <dd>{{ store.formatSyncMode(agent.nft.sync_mode) }}</dd>
        </div>
        <div>
          <dt>Market Mode</dt>
          <dd>{{ resolvedListing.market_mode }}</dd>
        </div>
        <div>
          <dt>tokenURI</dt>
          <dd>{{ store.getTokenMetadataUrl(resolvedListing.token_id) }}</dd>
        </div>
        <div v-if="resolvedListing.chain?.chain_listing_id">
          <dt>Chain Listing</dt>
          <dd>{{ resolvedListing.chain.chain_listing_id }}</dd>
        </div>
        <div v-if="resolvedListing.chain?.open_tx_hash">
          <dt>Open Tx</dt>
          <dd>{{ resolvedListing.chain.open_tx_hash }}</dd>
        </div>
        <div v-if="resolvedListing.chain?.close_tx_hash">
          <dt>Close Tx</dt>
          <dd>{{ resolvedListing.chain.close_tx_hash }}</dd>
        </div>
      </dl>
      <div class="action-row">
        <button class="primary-button" type="button" @click="store.buyListing(resolvedListing.id)">
          {{ resolvedListing.market_mode === "ONCHAIN" ? "Buy On-chain Listing" : "Buy Listing" }}
        </button>
        <button
          v-if="resolvedListing.status === 'OPEN'"
          class="ghost-button"
          type="button"
          @click="store.cancelListing(resolvedListing.id)"
        >
          {{ resolvedListing.market_mode === "ONCHAIN" ? "Cancel On-chain Listing" : "Cancel Listing" }}
        </button>
        <button class="ghost-button" type="button" @click="router.push(`/agents/${agent.id}`)">Agent Detail</button>
        <button class="ghost-button" type="button" @click="router.push(`/wallets/${resolvedListing.seller_wallet_id}`)">Seller Wallet</button>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Linked Agent</p>
          <h2>{{ agent.name }}</h2>
        </div>
        <span class="panel-chip">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
      </header>
      <dl class="detail-list detail-list-two">
        <div>
          <dt>Agent ID</dt>
          <dd>{{ agent.id }}</dd>
        </div>
        <div>
          <dt>Owner Wallet</dt>
          <dd>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</dd>
        </div>
        <div>
          <dt>Contract</dt>
          <dd>{{ agent.nft.contract_address || "Local only" }}</dd>
        </div>
        <div>
          <dt>Chain Token</dt>
          <dd>{{ agent.nft.chain_token_id || "Off-chain only" }}</dd>
        </div>
      </dl>
      <pre class="code-block">{{ agent.system_prompt }}</pre>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Market Timeline</p>
          <h2>Events & Transactions</h2>
        </div>
        <span class="panel-chip">{{ detail.events.length }} events</span>
      </header>
      <div v-if="detail.loading" class="empty-state">Loading listing timeline...</div>
      <div v-else-if="detail.error" class="empty-state">{{ detail.error }}</div>
      <div v-else class="page-grid page-grid-two">
        <div class="stack-grid">
          <article v-for="event in detail.events" :key="event.id" class="entity-card">
            <div class="entity-card-header">
              <strong>{{ event.event_type }}</strong>
              <span class="status-badge">{{ event.block_number || "pending" }}</span>
            </div>
            <dl class="detail-list detail-list-two">
              <div>
                <dt>Tx Hash</dt>
                <dd>{{ event.tx_hash }}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{{ store.formatDateTime(event.created_at) }}</dd>
              </div>
            </dl>
            <pre class="code-block">{{ JSON.stringify(event.payload, null, 2) }}</pre>
          </article>
          <div v-if="!detail.events.length" class="empty-state">No listing events have been indexed yet.</div>
        </div>

        <div class="stack-grid">
          <article v-for="tx in detail.transactions" :key="tx.id" class="entity-card">
            <div class="entity-card-header">
              <strong>{{ tx.tx_kind }}</strong>
              <span class="status-badge">{{ tx.status }}</span>
            </div>
            <dl class="detail-list detail-list-two">
              <div>
                <dt>Tx Hash</dt>
                <dd>{{ tx.tx_hash }}</dd>
              </div>
              <div>
                <dt>Updated</dt>
                <dd>{{ store.formatDateTime(tx.updated_at) }}</dd>
              </div>
              <div>
                <dt>From</dt>
                <dd>{{ tx.from_address || "Unavailable" }}</dd>
              </div>
              <div>
                <dt>To</dt>
                <dd>{{ tx.to_address || "Unavailable" }}</dd>
              </div>
            </dl>
            <pre class="code-block">{{ JSON.stringify(tx.payload, null, 2) }}</pre>
          </article>
          <div v-if="!detail.transactions.length" class="empty-state">No on-chain transactions have been indexed for this listing yet.</div>
        </div>
      </div>
    </section>
  </div>

  <section v-else class="panel">
    <div class="empty-state">{{ detail.error || "Listing not found in the current runtime state." }}</div>
  </section>
</template>

<script setup>
import { computed, reactive, watch, watchEffect } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();

const detail = reactive({
  loading: false,
  error: null,
  record: null,
  events: [],
  transactions: [],
});

const listingId = computed(() => String(route.params.listingId || ""));
const listing = computed(() => store.findListingById(listingId.value));
const resolvedListing = computed(() => detail.record || listing.value);
const agent = computed(() => (resolvedListing.value ? store.findAgentById(resolvedListing.value.agent_id) : null));
const holderState = computed(() => {
  if (!resolvedListing.value || !agent.value) {
    return "Unknown";
  }
  return resolvedListing.value.seller_wallet_id === agent.value.nft.owner_wallet_id ? "Aligned" : "Owner Drift";
});

watch(
  [listingId, () => store.state.listings.length],
  async () => {
    detail.loading = true;
    detail.error = null;
    detail.record = null;
    detail.events = [];
    detail.transactions = [];

    try {
      const payload = await store.fetchListingDetail(listingId.value);
      detail.record = payload.listing;
      detail.events = payload.events;
      detail.transactions = payload.transactions;
    } catch (error) {
      detail.error = error.message;
    } finally {
      detail.loading = false;
    }
  },
  { immediate: true }
);

watchEffect(() => {
  if (resolvedListing.value) {
    store.focusListing(resolvedListing.value.id);
  }
});
</script>
