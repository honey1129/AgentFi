<template>
  <div v-if="isUserView && resolvedListing && agent" class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>Ask price</span>
        <strong>{{ resolvedListing.price }}</strong>
        <p>The current market ask for token {{ resolvedListing.token_id }}.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Holder check</span>
        <strong>{{ holderState }}</strong>
        <p>{{ resolvedListing.seller_wallet_id === agent.nft.owner_wallet_id ? "Seller and current holder still match." : "Seller and holder have diverged. Review before trading." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Settlement mode</span>
        <strong>{{ resolvedListing.market_mode }}</strong>
        <p>{{ agent.nft.contract_address ? `Contract ${agent.nft.contract_address}` : "No on-chain contract is linked to this token yet." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Timeline</span>
        <strong>{{ detail.events.length }}</strong>
        <p>{{ detail.transactions.length }} indexed transactions for this listing.</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Listing</p>
              <h2>{{ resolvedListing.id }}</h2>
            </div>
            <span class="wallet-status-pill" :class="listingTone(resolvedListing.status)">{{ resolvedListing.status }}</span>
          </header>

          <div class="wallet-detail-hero">
            <div class="wallet-detail-media">
              <img :src="store.getTokenImageUrl(resolvedListing.token_id)" :alt="agent.name" />
            </div>

            <div class="wallet-detail-grid">
              <div class="wallet-detail-card">
                <span>Price</span>
                <strong>{{ resolvedListing.price }}</strong>
              </div>
              <div class="wallet-detail-card">
                <span>Token</span>
                <strong>{{ resolvedListing.token_id }}</strong>
              </div>
              <div class="wallet-detail-card">
                <span>Seller</span>
                <strong>{{ store.describeWallet(resolvedListing.seller_wallet_id) }}</strong>
              </div>
              <div class="wallet-detail-card">
                <span>Holder</span>
                <strong>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</strong>
              </div>
            </div>
          </div>

          <div class="wallet-card-actions">
            <button class="wallet-home-primary" type="button" @click="store.buyListing(resolvedListing.id)">
              {{ resolvedListing.market_mode === "ONCHAIN" ? "Buy on-chain listing" : "Buy listing" }}
            </button>
            <button
              v-if="resolvedListing.status === 'OPEN'"
              class="wallet-home-secondary"
              type="button"
              @click="store.cancelListing(resolvedListing.id)"
            >
              {{ resolvedListing.market_mode === "ONCHAIN" ? "Cancel on-chain listing" : "Cancel listing" }}
            </button>
            <button class="wallet-home-secondary" type="button" @click="router.push(`${routePrefix}/agents/${agent.id}`)">
              Agent detail
            </button>
          </div>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Linked agent</p>
              <h2>{{ agent.name }}</h2>
            </div>
            <span class="wallet-status-pill">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
          </header>

          <div class="wallet-detail-grid">
            <div class="wallet-detail-card">
              <span>Agent ID</span>
              <strong>{{ agent.id }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Chain token</span>
              <strong>{{ agent.nft.chain_token_id || "Off-chain only" }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Sync mode</span>
              <strong>{{ store.formatSyncMode(agent.nft.sync_mode) }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Contract</span>
              <strong>{{ agent.nft.contract_address || "Local only" }}</strong>
            </div>
          </div>

          <pre class="wallet-code-block">{{ agent.system_prompt }}</pre>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Market timeline</p>
              <h2>Events & transactions</h2>
            </div>
            <span class="wallet-status-pill">{{ detail.events.length }} events</span>
          </header>

          <div v-if="detail.loading" class="empty-state">Loading listing timeline...</div>
          <div v-else-if="detail.error" class="empty-state">{{ detail.error }}</div>
          <div v-else class="wallet-detail-timeline">
            <div class="wallet-inline-card">
              <span>Events</span>
              <strong>{{ detail.events.length }} indexed events</strong>
              <div v-if="!detail.events.length" class="wallet-side-empty">No listing events have been indexed yet.</div>
              <div v-else class="wallet-timeline-list">
                <article v-for="event in detail.events" :key="event.id" class="wallet-timeline-item">
                  <div class="wallet-timeline-head">
                    <strong>{{ event.event_type }}</strong>
                    <span>{{ event.block_number || "pending" }}</span>
                  </div>
                  <p>{{ store.formatDateTime(event.created_at) }}</p>
                  <pre class="wallet-code-block compact">{{ JSON.stringify(event.payload, null, 2) }}</pre>
                </article>
              </div>
            </div>

            <div class="wallet-inline-card">
              <span>Transactions</span>
              <strong>{{ detail.transactions.length }} indexed transactions</strong>
              <div v-if="!detail.transactions.length" class="wallet-side-empty">No on-chain transactions have been indexed for this listing yet.</div>
              <div v-else class="wallet-timeline-list">
                <article v-for="tx in detail.transactions" :key="tx.id" class="wallet-timeline-item">
                  <div class="wallet-timeline-head">
                    <strong>{{ tx.tx_kind }}</strong>
                    <span class="wallet-status-pill" :class="listingTone(tx.status)">{{ tx.status }}</span>
                  </div>
                  <p>{{ tx.tx_hash }} · {{ store.formatDateTime(tx.updated_at) }}</p>
                  <pre class="wallet-code-block compact">{{ JSON.stringify(tx.payload, null, 2) }}</pre>
                </article>
              </div>
            </div>
          </div>
        </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Settlement posture</div>
          <div class="wallet-side-list">
            <div>
              <strong>Market mode</strong>
              <span>{{ resolvedListing.market_mode }}</span>
            </div>
            <div>
              <strong>Chain listing</strong>
              <span>{{ resolvedListing.chain?.chain_listing_id || "Not indexed" }}</span>
            </div>
            <div>
              <strong>Open tx</strong>
              <span>{{ resolvedListing.chain?.open_tx_hash || "Not recorded" }}</span>
            </div>
            <div>
              <strong>Close tx</strong>
              <span>{{ resolvedListing.chain?.close_tx_hash || "Not recorded" }}</span>
            </div>
          </div>
        </article>

        <article class="wallet-side-card">
          <div class="wallet-side-title">Metadata route</div>
          <div class="wallet-side-list">
            <div>
              <strong>tokenURI</strong>
              <span>{{ store.getTokenMetadataUrl(resolvedListing.token_id) }}</span>
            </div>
            <div>
              <strong>Image</strong>
              <span>{{ store.getTokenImageUrl(resolvedListing.token_id) }}</span>
            </div>
          </div>
        </article>
      </aside>
    </section>
  </div>

  <div v-else-if="resolvedListing && agent" class="page-grid">
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
      <div class="stack-grid">
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
      </div>
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
        <button class="ghost-button" type="button" @click="router.push(`${routePrefix}/agents/${agent.id}`)">Agent Detail</button>
        <button
          v-if="!isUserView"
          class="ghost-button"
          type="button"
          @click="router.push(`/wallets/${resolvedListing.seller_wallet_id}`)"
        >
          Seller Wallet
        </button>
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
      <div class="stack-grid">
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
        <div class="surface-block">
          <p class="surface-kicker">Prompt</p>
          <h3 class="surface-title">System prompt</h3>
          <pre class="code-block compact-code-block">{{ agent.system_prompt }}</pre>
        </div>
      </div>
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
        <div class="panel-soft stack-grid">
          <div class="surface-block">
            <p class="surface-kicker">Events</p>
            <h3 class="surface-title">Index timeline</h3>
          </div>
          <div v-if="!detail.events.length" class="empty-state">No listing events have been indexed yet.</div>
          <div v-else class="data-table">
            <div class="data-table-head compact-log-table">
              <span>Event</span>
              <span>Block</span>
              <span>Created</span>
            </div>
            <template v-for="event in detail.events" :key="event.id">
              <article class="data-table-row compact-log-table">
                <div class="table-cell"><strong>{{ event.event_type }}</strong></div>
                <div class="table-cell"><span class="text-muted">{{ event.block_number || "pending" }}</span></div>
                <div class="table-cell"><span class="text-muted">{{ store.formatDateTime(event.created_at) }}</span></div>
              </article>
              <article class="data-table-row history-table-expanded">
                <div class="table-cell table-cell-full">
                  <pre class="code-block compact-code-block">{{ JSON.stringify(event.payload, null, 2) }}</pre>
                </div>
              </article>
            </template>
          </div>
        </div>

        <div class="panel-soft stack-grid">
          <div class="surface-block">
            <p class="surface-kicker">Transactions</p>
            <h3 class="surface-title">Chain settlement</h3>
          </div>
          <div v-if="!detail.transactions.length" class="empty-state">No on-chain transactions have been indexed for this listing yet.</div>
          <div v-else class="data-table">
            <div class="data-table-head tx-table">
              <span>Kind</span>
              <span>Status</span>
              <span>Hash</span>
              <span>Updated</span>
            </div>
            <template v-for="tx in detail.transactions" :key="tx.id">
              <article class="data-table-row tx-table">
                <div class="table-cell"><strong>{{ tx.tx_kind }}</strong></div>
                <div class="table-cell"><span class="status-badge">{{ tx.status }}</span></div>
                <div class="table-cell"><span class="text-muted">{{ tx.tx_hash }}</span></div>
                <div class="table-cell"><span class="text-muted">{{ store.formatDateTime(tx.updated_at) }}</span></div>
              </article>
              <article class="data-table-row history-table-expanded">
                <div class="table-cell table-cell-full">
                  <pre class="code-block compact-code-block">{{ JSON.stringify(tx.payload, null, 2) }}</pre>
                </div>
              </article>
            </template>
          </div>
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
const isUserView = computed(() => route.meta.audience === "user");
const routePrefix = computed(() => (isUserView.value ? "/app" : ""));

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

function listingTone(status) {
  if (status === "OPEN" || status === "RUNNING" || status === "PENDING") {
    return "is-pending";
  }
  if (status === "SOLD" || status === "COMPLETED" || status === "CONFIRMED") {
    return "is-completed";
  }
  return "is-review";
}
</script>
