<template>
  <div v-if="isUserView" class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>Session</span>
        <strong>{{ store.authenticated.value ? "Ready" : "Unsigned" }}</strong>
        <p>{{ store.authenticated.value ? "This wallet can submit protected actions." : "Sign a challenge before creating, listing, or transferring." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Connected address</span>
        <strong>{{ store.state.metamask.address ? store.truncate(store.state.metamask.address, 18) : "Not connected" }}</strong>
        <p>{{ store.state.metamask.chainId ? `Chain ${store.state.metamask.chainId}` : "No wallet connected in this browser." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Chain sync</span>
        <strong>{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</strong>
        <p>{{ store.state.runtime?.nft_contract_address || "NFT contract not configured." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Marketplace</span>
        <strong>{{ store.state.runtime?.marketplace_contract_address ? "Configured" : "Unavailable" }}</strong>
        <p>{{ store.state.runtime?.marketplace_contract_address || "No marketplace contract configured." }}</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
      <article class="wallet-card">
        <header class="wallet-card-header">
          <div>
            <p class="wallet-card-kicker">Wallet</p>
            <h2>MetaMask sign-in</h2>
          </div>
          <button class="wallet-home-secondary" type="button" @click="store.connectMetaMask(true)">Connect MetaMask</button>
        </header>

        <form class="wallet-form-grid" @submit.prevent="submitWallet">
          <label class="wallet-field">
            <span>Wallet label</span>
            <input v-model="walletForm.label" placeholder="main_operator" />
          </label>
          <label class="wallet-field">
            <span>Bootstrap balance</span>
            <input v-model="walletForm.initialBalance" type="number" min="0" step="0.01" />
          </label>
          <label class="wallet-field wallet-field-full">
            <span>Connected address</span>
            <input :value="store.state.metamask.address || ''" placeholder="0x..." readonly />
          </label>
          <div class="wallet-form-actions wallet-field-full">
            <button class="wallet-home-secondary" type="button" @click="store.connectMetaMask(true)">Connect</button>
            <button class="wallet-home-primary" type="submit">Sign in &amp; sync</button>
            <button class="wallet-home-secondary" type="button" @click="store.logoutMetaMask(true)">Logout</button>
          </div>
        </form>
      </article>

      <article class="wallet-card">
        <header class="wallet-card-header">
          <div>
            <p class="wallet-card-kicker">Readiness</p>
            <h2>Wallet status</h2>
          </div>
          <span class="wallet-status-pill is-pending">{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</span>
        </header>

        <div class="wallet-status-grid">
          <article class="wallet-status-card">
            <span>MetaMask address</span>
            <strong>{{ store.state.metamask.address ? store.truncate(store.state.metamask.address, 18) : "Not connected" }}</strong>
            <p>{{ store.state.metamask.chainId || "No chain detected" }}</p>
          </article>
          <article class="wallet-status-card">
            <span>Runtime wallet</span>
            <strong>{{ store.state.metamask.wallet?.name || store.state.metamask.wallet?.id || "Not mapped" }}</strong>
            <p>{{ store.authenticated.value ? "Session verified for protected writes." : "No signed runtime session." }}</p>
          </article>
          <article class="wallet-status-card">
            <span>NFT contract</span>
            <strong>{{ store.state.runtime?.nft_contract_address ? "Ready" : "Missing" }}</strong>
            <p>{{ store.state.runtime?.nft_contract_address || "No NFT contract configured." }}</p>
          </article>
          <article class="wallet-status-card">
            <span>Auto mint</span>
            <strong>{{ store.state.runtime?.auto_onchain_mint_enabled ? "Enabled" : "Disabled" }}</strong>
            <p>{{ store.state.runtime?.marketplace_contract_address || "No marketplace contract configured." }}</p>
          </article>
        </div>
      </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Session checklist</div>
          <div class="wallet-side-list">
            <div>
              <strong>Connect wallet</strong>
              <span>Attach MetaMask to this browser session.</span>
            </div>
            <div>
              <strong>Verify chain</strong>
              <span>Ensure the wallet is aligned with the runtime chain.</span>
            </div>
            <div>
              <strong>Sign challenge</strong>
              <span>Unlock protected creation, listing, and transfer actions.</span>
            </div>
          </div>
        </article>
      </aside>
    </section>
  </div>

  <div v-else class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Session</span>
        <strong>{{ store.authenticated.value ? "Signed" : "Unsigned" }}</strong>
        <p>{{ store.authenticated.value ? "Current browser wallet can submit protected writes." : "Sign a challenge before creating, listing, or transferring." }}</p>
      </article>
      <article class="metric-card">
        <span>Address</span>
        <strong>{{ store.state.metamask.address ? store.truncate(store.state.metamask.address, 16) : "Not connected" }}</strong>
        <p>{{ store.state.metamask.chainId ? `Chain ${store.state.metamask.chainId}` : "No wallet connected in this browser." }}</p>
      </article>
      <article class="metric-card">
        <span>Chain Sync</span>
        <strong>{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</strong>
        <p>{{ store.state.runtime?.nft_contract_address || "NFT contract not configured for this runtime." }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Authenticate</p>
          <h2>MetaMask Sign-In</h2>
        </div>
        <button class="ghost-button" type="button" @click="store.connectMetaMask(true)">Connect MetaMask</button>
      </header>
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
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Readiness</p>
          <h2>Operator Readiness</h2>
        </div>
        <span class="panel-chip">{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</span>
      </header>
      <div class="stack-grid">
        <div class="surface-block">
          <p class="surface-kicker">Connection</p>
          <h3 class="surface-title">Browser wallet</h3>
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
          </dl>
        </div>
        <div class="surface-block">
          <p class="surface-kicker">Chain Setup</p>
          <h3 class="surface-title">Runtime configuration</h3>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Chain Sync</dt>
              <dd>{{ store.state.runtime?.chain_sync_state || "DISABLED" }}</dd>
            </div>
            <div>
              <dt>NFT Contract</dt>
              <dd>{{ store.state.runtime?.nft_contract_address || "Not configured" }}</dd>
            </div>
            <div>
              <dt>Marketplace</dt>
              <dd>{{ store.state.runtime?.marketplace_contract_address || "Not configured" }}</dd>
            </div>
            <div>
              <dt>Auto Mint</dt>
              <dd>{{ store.state.runtime?.auto_onchain_mint_enabled ? "Enabled" : "Disabled" }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";
import { useRoute } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();
const route = useRoute();
const isUserView = computed(() => route.meta.audience === "user");

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
