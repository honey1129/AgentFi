<template>
  <div class="page-grid page-grid-two">
    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Actions</p>
          <h2>Market Actions</h2>
        </div>
        <span class="panel-chip">{{ store.state.listings.length }} live listings</span>
      </header>
      <p class="panel-intro">
        Keep listing and buying in the same focused workspace. The left side is purely transactional; the right side shows the market inventory and the currently selected NFT.
      </p>
      <div class="stack-grid">
        <div class="surface-block">
          <p class="surface-kicker">List Ownership</p>
          <h3 class="surface-title">Price an NFT-backed agent for sale</h3>
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
              <p class="field-note">
                {{ listingRouteHint }}
              </p>
            </div>
            <div class="action-row field-full">
              <button class="primary-button" type="submit">{{ listingActionLabel }}</button>
            </div>
          </form>
        </div>

        <div class="surface-block">
          <p class="surface-kicker">Acquire Control</p>
          <h3 class="surface-title">Buy an open listing</h3>
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
              <p class="field-note">
                {{ buyRouteHint }}
              </p>
            </div>
            <div class="action-row field-full">
              <button class="primary-button" type="submit">{{ buyActionLabel }}</button>
            </div>
          </form>
        </div>

        <div v-if="store.state.marketplace.pendingTx" class="surface-block">
          <p class="surface-kicker">Transaction</p>
          <h3 class="surface-title">Latest market transaction</h3>
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

        <div class="empty-state">
          Direct ownership transfers now live on the dedicated <strong>Transfers</strong> page so listing actions stay focused on pricing and buying.
        </div>
      </div>
    </section>

    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Market</p>
          <h2>Marketplace</h2>
        </div>
      </header>
      <p class="panel-intro">
        This side is intentionally visual: a focused hero listing first, then the remaining inventory below. Use it like a curated board instead of a raw table.
      </p>
      <div v-if="store.selectedListing.value" class="spotlight-card">
        <div class="spotlight-media">
          <img
            :src="store.getTokenImageUrl(store.selectedListing.value.token_id)"
            :alt="store.findAgentById(store.selectedListing.value.agent_id)?.name || 'Agent NFT'"
          />
        </div>
        <div class="spotlight-copy">
          <div class="entity-card-header">
            <strong>{{ store.findAgentById(store.selectedListing.value.agent_id)?.name || store.selectedListing.value.agent_id }}</strong>
            <span class="status-badge">{{ store.selectedListing.value.status }}</span>
          </div>
          <dl class="detail-list">
            <div>
              <dt>Listing ID</dt>
              <dd>{{ store.selectedListing.value.id }}</dd>
            </div>
            <div>
              <dt>Price</dt>
              <dd>{{ store.selectedListing.value.price }}</dd>
            </div>
            <div>
              <dt>Seller</dt>
              <dd>{{ store.describeWallet(store.selectedListing.value.seller_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Current Holder</dt>
              <dd>{{ store.describeWallet(store.findAgentById(store.selectedListing.value.agent_id)?.nft.owner_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Chain Status</dt>
              <dd>{{ store.formatSyncMode(store.findAgentById(store.selectedListing.value.agent_id)?.nft.sync_mode) }}</dd>
            </div>
            <div>
              <dt>Market Mode</dt>
              <dd>{{ store.selectedListing.value.market_mode }}</dd>
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
            <button class="ghost-button" type="button" @click="router.push(`/market/listings/${store.selectedListing.value.id}`)">Detail</button>
            <button
              class="ghost-button"
              type="button"
              @click="router.push(`/agents/${store.selectedListing.value.agent_id}`)"
            >
              View Agent Detail
            </button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        No open listings. List an NFT-backed agent to populate the market.
      </div>

      <div v-if="store.state.listings.length" class="entity-grid">
        <article
          v-for="listing in store.state.listings"
          :key="listing.id"
          class="entity-card"
          :class="{ 'entity-card-focused': store.selectedListing.value?.id === listing.id }"
        >
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
              <dt>NFT</dt>
              <dd>{{ listing.token_id }}</dd>
            </div>
            <div>
              <dt>Seller</dt>
              <dd>{{ store.describeWallet(listing.seller_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{{ listing.status }}</dd>
            </div>
            <div>
              <dt>Mode</dt>
              <dd>{{ listing.market_mode }}</dd>
            </div>
          </dl>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="store.focusListing(listing.id)">Focus</button>
            <button class="ghost-button" type="button" @click="router.push(`/market/listings/${listing.id}`)">Detail</button>
            <button class="ghost-button" type="button" @click="buyFromCard(listing.id)">
              {{ listing.market_mode === "ONCHAIN" ? "Buy On-chain" : "Buy" }}
            </button>
          </div>
        </article>
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
