<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Open Listings</span>
        <strong>{{ store.state.listings.length }}</strong>
        <p>Listings currently available in the ownership market.</p>
      </article>
      <article class="metric-card">
        <span>On-chain</span>
        <strong>{{ onChainListingsCount }}</strong>
        <p>Listings that settle through the marketplace contract.</p>
      </article>
      <article class="metric-card">
        <span>Selected</span>
        <strong>{{ store.selectedListing.value?.price || "None" }}</strong>
        <p>{{ store.selectedListing.value ? "Focused listing ready for action." : "Select a listing to inspect details." }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Open Listing</p>
          <h2>List Ownership</h2>
        </div>
        <span class="panel-chip">{{ listingActionLabel }}</span>
      </header>
      <form class="form-grid compact-grid" @submit.prevent="submitListing">
        <label class="field field-full">
          <span>NFT</span>
          <select v-model="listingForm.token_id" required>
            <option disabled value="">Select an NFT</option>
            <option v-for="agent in store.state.agents" :key="agent.nft.token_id" :value="agent.nft.token_id">
              {{ agent.name }} · {{ agent.nft.token_id }}
            </option>
          </select>
        </label>
        <label class="field field-full">
          <span>Price</span>
          <input v-model="listingForm.price" type="number" min="0.01" step="0.01" required />
        </label>
        <div class="field field-full">
          <p class="field-note">{{ listingRouteHint }}</p>
        </div>
        <div class="action-row field-full">
          <button class="primary-button" type="submit">{{ listingActionLabel }}</button>
        </div>
      </form>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Acquire Control</p>
          <h2>Buy Listing</h2>
        </div>
        <span class="panel-chip">{{ buyActionLabel }}</span>
      </header>
      <form class="form-grid compact-grid" @submit.prevent="submitBuy">
        <label class="field field-full">
          <span>Listing</span>
          <select v-model="buyForm.listing_id" required>
            <option disabled value="">Select a listing</option>
            <option v-for="listing in store.state.listings" :key="listing.id" :value="listing.id">
              {{ listing.id }} · {{ listing.price }}
            </option>
          </select>
        </label>
        <div class="field field-full">
          <p class="field-note">{{ buyRouteHint }}</p>
        </div>
        <div class="action-row field-full">
          <button class="primary-button" type="submit">{{ buyActionLabel }}</button>
        </div>
      </form>
      <div v-if="store.state.marketplace.pendingTx" class="surface-block">
        <p class="surface-kicker">Latest Transaction</p>
        <h3 class="surface-title">Pending chain activity</h3>
        <dl class="detail-list">
          <div>
            <dt>Kind</dt>
            <dd>{{ store.state.marketplace.pendingTx.kind }}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{{ store.state.marketplace.pendingTx.status }}</dd>
          </div>
          <div>
            <dt>Tx Hash</dt>
            <dd>{{ store.state.marketplace.pendingTx.txHash }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Inventory</p>
          <h2>Open Market Listings</h2>
        </div>
        <span class="panel-chip">{{ store.state.listings.length }} available</span>
      </header>
      <div v-if="!store.state.listings.length" class="empty-state">
        No open listings. List an NFT-backed agent to populate the market.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head market-table">
          <span>Listing</span>
          <span>Agent</span>
          <span>Seller</span>
          <span>Mode</span>
          <span>Price</span>
          <span>Actions</span>
        </div>
        <article
          v-for="listing in store.state.listings"
          :key="listing.id"
          class="data-table-row market-table"
          :class="{ 'is-selected': store.selectedListing.value?.id === listing.id }"
        >
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ listing.id }}</strong>
              <span class="text-muted">{{ listing.status }}</span>
            </div>
          </div>
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ store.findAgentById(listing.agent_id)?.name || listing.agent_id }}</strong>
              <span class="text-muted">{{ listing.token_id }}</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ store.describeWallet(listing.seller_wallet_id) }}</span>
          </div>
          <div class="table-cell">
            <span class="status-badge">{{ listing.market_mode }}</span>
          </div>
          <div class="table-cell">
            <strong>{{ listing.price }}</strong>
          </div>
          <div class="table-cell">
            <div class="table-actions">
              <button class="ghost-button" type="button" @click="store.focusListing(listing.id)">Select</button>
              <button class="ghost-button" type="button" @click="router.push(`/market/listings/${listing.id}`)">Detail</button>
              <button class="ghost-button" type="button" @click="buyFromCard(listing.id)">
                {{ listing.market_mode === "ONCHAIN" ? "Buy On-chain" : "Buy" }}
              </button>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section v-if="store.selectedListing.value" class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Selected Listing</p>
          <h2>{{ store.findAgentById(store.selectedListing.value.agent_id)?.name || store.selectedListing.value.agent_id }}</h2>
        </div>
        <span class="panel-chip">{{ store.selectedListing.value.status }}</span>
      </header>
      <div class="spotlight-card admin-spotlight-card">
        <div class="spotlight-media">
          <img
            :src="store.getTokenImageUrl(store.selectedListing.value.token_id)"
            :alt="store.findAgentById(store.selectedListing.value.agent_id)?.name || 'Agent NFT'"
          />
        </div>
        <div class="spotlight-copy">
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Price</dt>
              <dd>{{ store.selectedListing.value.price }}</dd>
            </div>
            <div>
              <dt>Seller</dt>
              <dd>{{ store.describeWallet(store.selectedListing.value.seller_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Holder</dt>
              <dd>{{ store.describeWallet(store.findAgentById(store.selectedListing.value.agent_id)?.nft.owner_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Mode</dt>
              <dd>{{ store.selectedListing.value.market_mode }}</dd>
            </div>
            <div>
              <dt>Sync</dt>
              <dd>{{ store.formatSyncMode(store.findAgentById(store.selectedListing.value.agent_id)?.nft.sync_mode) }}</dd>
            </div>
            <div>
              <dt>tokenURI</dt>
              <dd>{{ store.getTokenMetadataUrl(store.selectedListing.value.token_id) }}</dd>
            </div>
            <div v-if="store.selectedListing.value.chain?.chain_listing_id">
              <dt>Chain Listing</dt>
              <dd>{{ store.selectedListing.value.chain.chain_listing_id }}</dd>
            </div>
            <div v-if="store.selectedListing.value.chain?.open_tx_hash">
              <dt>Open Tx</dt>
              <dd>{{ store.selectedListing.value.chain.open_tx_hash }}</dd>
            </div>
          </dl>
          <div class="action-row">
            <button class="primary-button" type="button" @click="buyFromCard(store.selectedListing.value.id)">
              {{ store.selectedListing.value.market_mode === "ONCHAIN" ? "Buy On-chain" : "Buy Listing" }}
            </button>
            <button class="ghost-button" type="button" @click="router.push(`/market/listings/${store.selectedListing.value.id}`)">Open Detail</button>
            <button class="ghost-button" type="button" @click="router.push(`/agents/${store.selectedListing.value.agent_id}`)">Open Agent</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();

const listingForm = reactive({
  token_id: "",
  price: "250",
});

const buyForm = reactive({
  listing_id: "",
});

const selectedAgentForListing = computed(() => store.state.agents.find((agent) => agent.nft.token_id === listingForm.token_id) || null);
const selectedListingForBuy = computed(() => store.findListingById(buyForm.listing_id) || null);
const listingActionLabel = computed(() =>
  selectedAgentForListing.value && store.shouldUseOnChainListing(selectedAgentForListing.value.nft) ? "Open On-chain Listing" : "Open Listing"
);
const onChainListingsCount = computed(() => store.state.listings.filter((listing) => listing.market_mode === "ONCHAIN").length);
const listingRouteHint = computed(() =>
  selectedAgentForListing.value && store.shouldUseOnChainListing(selectedAgentForListing.value.nft)
    ? "This NFT is chain-synced. The flow will request NFT approval and then submit a real on-chain marketplace listing with MetaMask."
    : "This NFT will use the local runtime marketplace flow."
);
const buyActionLabel = computed(() =>
  selectedListingForBuy.value?.market_mode === "ONCHAIN" ? "Buy On-chain Listing" : "Buy Listing"
);
const buyRouteHint = computed(() =>
  selectedListingForBuy.value?.market_mode === "ONCHAIN"
    ? "This purchase will submit a real on-chain marketplace transaction in MetaMask."
    : "This listing will settle through the local runtime marketplace."
);

watch(
  () => route.query,
  (query) => {
    if (typeof query.token_id === "string") {
      listingForm.token_id = query.token_id;
    }
    if (typeof query.listing_id === "string") {
      buyForm.listing_id = query.listing_id;
      store.focusListing(query.listing_id);
    }
  },
  { immediate: true }
);

async function submitListing() {
  await store.openListing({
    token_id: listingForm.token_id,
    price: listingForm.price,
  });
}

async function submitBuy() {
  await store.buyListing(buyForm.listing_id);
}

async function buyFromCard(listingId) {
  buyForm.listing_id = listingId;
  await store.buyListing(listingId);
}
</script>
