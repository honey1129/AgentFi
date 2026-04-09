<template>
  <div class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>My listings</span>
        <strong>{{ myListings.length }}</strong>
        <p>Live sell-side inventory opened by the current wallet.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Buyable</span>
        <strong>{{ buyableListings.length }}</strong>
        <p>Listings currently available from external operators.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Sellable</span>
        <strong>{{ ownedAgents.length }}</strong>
        <p>Owned NFTs eligible for listing or direct transfer.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Latest tx</span>
        <strong>{{ store.state.marketplace.pendingTx?.kind || "Idle" }}</strong>
        <p>{{ store.state.marketplace.pendingTx?.status || "No pending market transaction." }}</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Inventory</p>
              <h2>Open market inventory</h2>
            </div>
            <span class="wallet-status-pill">{{ buyableListings.length }} listings</span>
          </header>

          <p class="wallet-card-copy">
            Review open listings first, then route into sell-side or buy-side actions from the sections below.
          </p>

          <div class="wallet-home-table-shell">
            <div class="wallet-home-table-head wallet-market-table">
              <div>Listing</div>
              <div>Seller</div>
              <div>Price</div>
              <div>Mode</div>
              <div>Actions</div>
            </div>

            <div
              v-for="listing in buyableListings"
              :key="listing.id"
              class="wallet-home-table-row wallet-market-table"
            >
              <div>
                <strong>{{ store.findAgentById(listing.agent_id)?.name || listing.agent_id }}</strong>
                <span>{{ listing.id }}</span>
              </div>
              <div>{{ store.describeWallet(listing.seller_wallet_id) }}</div>
              <div>{{ listing.price }}</div>
              <div>{{ listing.market_mode }}</div>
              <div class="wallet-home-inline-meta">
                <button class="wallet-table-button" type="button" @click="prefillBuy(listing.id)">Use</button>
                <RouterLink :to="`/app/market/listings/${listing.id}`">Detail</RouterLink>
              </div>
            </div>

            <div v-if="!buyableListings.length" class="empty-state">
              No external listings are available to buy right now.
            </div>
          </div>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Sell</p>
              <h2>Open a listing</h2>
            </div>
            <span class="wallet-status-pill is-pending">{{ listingActionLabel }}</span>
          </header>

          <p class="wallet-card-copy">
            Select one of your NFTs, set a price, and route it through the runtime or on-chain listing path.
          </p>

          <form class="wallet-form-grid" @submit.prevent="submitListing">
            <label class="wallet-field wallet-field-full">
              <span>Owned NFT</span>
              <select v-model="listingForm.token_id" required>
                <option disabled value="">Select one of your NFTs</option>
                <option v-for="agent in ownedAgents" :key="agent.nft.token_id" :value="agent.nft.token_id">
                  {{ agent.name }} · {{ agent.nft.token_id }}
                </option>
              </select>
            </label>
            <label class="wallet-field wallet-field-full">
              <span>Price</span>
              <input v-model="listingForm.price" type="number" min="0.01" step="0.01" required />
            </label>
            <div class="wallet-form-note wallet-field-full">{{ listingRouteHint }}</div>
            <div class="wallet-form-actions wallet-field-full">
              <button class="wallet-home-primary" type="submit">{{ listingActionLabel }}</button>
            </div>
          </form>

          <div v-if="selectedAgentForListing" class="wallet-inline-card">
            <span>Selected inventory</span>
            <strong>{{ selectedAgentForListing.name }}</strong>
            <p>{{ store.truncate(selectedAgentForListing.system_prompt, 140) }}</p>
          </div>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Buy</p>
              <h2>Acquire from market</h2>
            </div>
            <span class="wallet-status-pill is-completed">{{ buyActionLabel }}</span>
          </header>

          <p class="wallet-card-copy">
            Use the current market inventory to prefill a purchase, then route the buy flow through the correct settlement path.
          </p>

          <form class="wallet-form-grid" @submit.prevent="submitBuy">
            <label class="wallet-field wallet-field-full">
              <span>Market listing</span>
              <select v-model="buyForm.listing_id" required>
                <option disabled value="">Select a listing</option>
                <option v-for="listing in buyableListings" :key="listing.id" :value="listing.id">
                  {{ listing.id }} · {{ listing.price }}
                </option>
              </select>
            </label>
            <div class="wallet-form-note wallet-field-full">{{ buyRouteHint }}</div>
            <div class="wallet-form-actions wallet-field-full">
              <button class="wallet-home-primary" type="submit">{{ buyActionLabel }}</button>
              <button class="wallet-home-secondary" type="button" @click="router.push('/app/transfers')">Direct transfer</button>
            </div>
          </form>

          <div v-if="selectedListingForBuy" class="wallet-inline-card">
            <span>Selected listing</span>
            <strong>{{ store.findAgentById(selectedListingForBuy.agent_id)?.name || selectedListingForBuy.agent_id }}</strong>
            <p>Seller: {{ store.describeWallet(selectedListingForBuy.seller_wallet_id) }} · Price: {{ selectedListingForBuy.price }}</p>
          </div>
          <div v-else-if="store.state.marketplace.pendingTx" class="wallet-inline-card">
            <span>Pending transaction</span>
            <strong>{{ store.state.marketplace.pendingTx.kind }}</strong>
            <p>{{ store.state.marketplace.pendingTx.status }} · {{ store.state.marketplace.pendingTx.txHash }}</p>
          </div>
        </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Your listings</div>
          <div class="wallet-side-list">
            <div v-for="listing in myListings.slice(0, 5)" :key="listing.id">
              <strong>{{ store.findAgentById(listing.agent_id)?.name || listing.agent_id }}</strong>
              <span>{{ listing.price }} · {{ listing.status }}</span>
            </div>
            <div v-if="!myListings.length" class="wallet-side-empty">No open listings from this wallet yet.</div>
          </div>
        </article>

        <article class="wallet-side-card">
          <div class="wallet-side-title">Market routing</div>
          <div class="wallet-side-list">
            <div>
              <strong>Listing path</strong>
              <span>{{ listingRouteHint }}</span>
            </div>
            <div>
              <strong>Buy path</strong>
              <span>{{ buyRouteHint }}</span>
            </div>
            <div>
              <strong>Pending tx</strong>
              <span>{{ store.state.marketplace.pendingTx?.txHash || "No pending transaction." }}</span>
            </div>
          </div>
        </article>
      </aside>
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

const currentWalletId = computed(() => store.state.metamask.wallet?.id || null);
const ownedAgents = computed(() =>
  currentWalletId.value ? store.state.agents.filter((agent) => agent.nft.owner_wallet_id === currentWalletId.value) : []
);
const myListings = computed(() =>
  currentWalletId.value ? store.state.listings.filter((listing) => listing.seller_wallet_id === currentWalletId.value) : []
);
const buyableListings = computed(() =>
  currentWalletId.value ? store.state.listings.filter((listing) => listing.seller_wallet_id !== currentWalletId.value) : store.state.listings
);

const selectedAgentForListing = computed(() => ownedAgents.value.find((agent) => agent.nft.token_id === listingForm.token_id) || null);
const selectedListingForBuy = computed(() => buyableListings.value.find((listing) => listing.id === buyForm.listing_id) || null);
const listingActionLabel = computed(() =>
  selectedAgentForListing.value && store.shouldUseOnChainListing(selectedAgentForListing.value.nft) ? "Open on-chain listing" : "Open listing"
);
const buyActionLabel = computed(() =>
  selectedListingForBuy.value?.market_mode === "ONCHAIN" ? "Buy on-chain listing" : "Buy listing"
);
const listingRouteHint = computed(() =>
  selectedAgentForListing.value && store.shouldUseOnChainListing(selectedAgentForListing.value.nft)
    ? "This NFT is chain-synced. The flow will request an on-chain listing transaction."
    : "This NFT will use the runtime listing path."
);
const buyRouteHint = computed(() =>
  selectedListingForBuy.value?.market_mode === "ONCHAIN"
    ? "Buying this listing will route through MetaMask on the configured chain."
    : "Buying this listing will use the runtime settlement flow."
);

watch(
  () => route.query,
  (query) => {
    if (typeof query.token_id === "string") {
      listingForm.token_id = query.token_id;
    }
    if (typeof query.listing_id === "string") {
      buyForm.listing_id = query.listing_id;
    }
  },
  { immediate: true }
);

async function submitListing() {
  await store.openListing(listingForm.token_id, listingForm.price);
}

async function submitBuy() {
  await store.buyListing(buyForm.listing_id);
}

function prefillBuy(listingId) {
  buyForm.listing_id = listingId;
}
</script>
