<template>
  <div class="app-shell user-app-shell wallet-ui-shell" :class="themeClass">
    <header class="wallet-ui-topbar">
      <div class="wallet-ui-topbar-inner">
        <div class="wallet-ui-brand">
          <div class="wallet-ui-brand-mark">{{ brandMark }}</div>
          <div class="wallet-ui-brand-copy">
            <strong>{{ brandTitle }}</strong>
            <span>{{ brandKicker }}</span>
          </div>
        </div>

        <nav class="wallet-ui-product-nav" aria-label="Primary">
          <RouterLink
            v-for="item in productItems"
            :key="item.to"
            :to="item.to"
            class="wallet-ui-product-link"
            :class="{ 'is-active': currentSection === item.section }"
          >
            <span class="wallet-ui-product-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>

        <div ref="walletControlRef" class="wallet-ui-top-actions">
          <button
            class="wallet-ui-wallet-trigger"
            :class="walletControlStateClass"
            type="button"
            :aria-expanded="walletMenuOpen ? 'true' : 'false'"
            @click="toggleWalletMenu"
          >
            <div class="wallet-ui-wallet-trigger-main">
              <div class="wallet-ui-wallet-avatar">{{ brandMark }}</div>
              <div class="wallet-ui-wallet-trigger-copy">
                <strong>{{ walletTriggerTitle }}</strong>
                <span>{{ walletTriggerSubtitle }}</span>
              </div>
            </div>

            <div class="wallet-ui-wallet-trigger-side">
              <span class="wallet-ui-wallet-status" :class="walletControlStateClass">
                {{ walletStatusLabel }}
              </span>
              <span class="wallet-ui-wallet-caret">{{ walletMenuOpen ? "▴" : "▾" }}</span>
            </div>
          </button>

          <div v-if="walletMenuOpen" class="wallet-ui-wallet-dropdown" :class="walletControlStateClass">
            <div class="wallet-ui-wallet-dropdown-meta">
              <div class="wallet-ui-wallet-dropdown-row is-primary">
                <strong class="wallet-ui-wallet-address">
                  {{ walletAddress ? truncateAddress(walletAddress, 18) : "Not connected" }}
                </strong>
                <span class="wallet-ui-wallet-status" :class="walletControlStateClass">
                  {{ walletStatusLabel }}
                </span>
              </div>
              <div class="wallet-ui-wallet-dropdown-row">
                <div class="wallet-ui-wallet-chain">
                  <span class="wallet-ui-wallet-chain-dot" :class="walletChainTone"></span>
                  <strong>{{ walletChainLabel }}</strong>
                </div>
                <button
                  v-if="walletAddress"
                  class="wallet-ui-wallet-copy"
                  type="button"
                  @click.stop="handleCopyAddress"
                >
                  {{ copyAddressLabel }}
                </button>
              </div>
            </div>

            <div class="wallet-ui-wallet-dropdown-actions">
              <button class="wallet-ui-wallet-cta" type="button" @click="handleWalletPrimaryAction">
                {{ walletPrimaryActionLabel }}
              </button>
              <button
                v-if="walletAuthenticated"
                class="wallet-ui-ghost-action"
                type="button"
                @click="handleLogout"
              >
                Logout
              </button>
              <button
                v-else-if="walletConnected"
                class="wallet-ui-ghost-action"
                type="button"
                @click="handleWalletSwitch"
              >
                Switch wallet
              </button>
              <RouterLink
                v-else-if="portalTo && portalLabel"
                :to="portalTo"
                class="wallet-ui-ghost-action"
                @click="closeWalletMenu"
              >
                {{ portalLabel }}
              </RouterLink>
              <button v-else class="wallet-ui-ghost-action" type="button" @click="closeWalletMenu">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="wallet-ui-main-grid">
      <aside class="wallet-ui-side-rail">
        <RouterLink
          v-for="item in sideItems"
          :key="item.to"
          :to="item.to"
          class="wallet-ui-side-link"
          :class="{ 'is-active': isSideActive(item) }"
        >
          <span class="wallet-ui-side-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </aside>

      <main class="wallet-ui-content">
        <section class="wallet-ui-page-header">
          <div class="wallet-ui-page-copy">
            <div class="wallet-ui-page-title">{{ title || "Overview" }}</div>
            <div class="wallet-ui-page-description">
              {{ description || headline || "Multi-account, multi-network portfolio tracking with NFTs, activity, and security review." }}
            </div>
          </div>

          <div class="wallet-ui-page-tools">
            <label class="wallet-ui-search">
              <span>⌕</span>
              <input type="text" :placeholder="searchPlaceholder" />
            </label>
            <button class="wallet-ui-filter" type="button">
              {{ networkSummary }}
              <span>▾</span>
            </button>
            <button class="wallet-ui-filter" type="button">
              {{ unitSummary }}
              <span>▾</span>
            </button>
          </div>
        </section>

        <slot />
      </main>
    </div>

    <footer class="wallet-ui-footer">
      <div class="wallet-ui-footer-brand">
        <div class="wallet-ui-footer-mark">{{ brandMark }}</div>
        <div>
          <strong>{{ brandTitle }}</strong>
          <span>Wallet-first workspace for NFT-backed operators.</span>
        </div>
      </div>

      <div class="wallet-ui-footer-links">
        <RouterLink to="/app/create">New Agent</RouterLink>
        <RouterLink to="/app/market">Market</RouterLink>
        <RouterLink to="/app/runs">Runs</RouterLink>
        <RouterLink to="/runtime/overview">Admin</RouterLink>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const emit = defineEmits(["refresh", "connect-wallet", "sign-wallet", "logout-wallet"]);

const props = defineProps({
  themeClass: {
    type: String,
    required: true,
  },
  currentSection: {
    type: String,
    default: null,
  },
  activeSubsection: {
    type: String,
    default: null,
  },
  accessSummary: {
    type: String,
    required: true,
  },
  walletConnected: {
    type: Boolean,
    default: false,
  },
  walletAuthenticated: {
    type: Boolean,
    default: false,
  },
  walletAddress: {
    type: String,
    default: "",
  },
  walletChainId: {
    type: String,
    default: "",
  },
  title: {
    type: String,
    default: "Overview",
  },
  headline: {
    type: String,
    default: "",
  },
  description: {
    type: String,
    default: "",
  },
  helperText: {
    type: String,
    required: true,
  },
  refreshing: {
    type: Boolean,
    default: false,
  },
  brandMark: {
    type: String,
    default: "AI",
  },
  brandKicker: {
    type: String,
    default: "AgentFi App",
  },
  brandTitle: {
    type: String,
    default: "User Workspace",
  },
  portalLabel: {
    type: String,
    default: "",
  },
  portalTo: {
    type: String,
    default: "",
  },
});

const productItems = [
  { section: "home", label: "Home", to: "/app/home", icon: "◎" },
  { section: "create", label: "New Agent", to: "/app/create", icon: "＋" },
  { section: "market", label: "Market", to: "/app/market", icon: "↺" },
  { section: "runs", label: "Runs", to: "/app/runs", icon: "◔" },
];

const sideItems = [
  { section: "home", label: "Portfolio", to: "/app/home", icon: "◫" },
  { section: "agents", label: "Agents", to: "/app/agents", icon: "◈" },
  { section: "market", subsection: "market", label: "NFTs", to: "/app/market", icon: "▣" },
  { section: "market", subsection: "transfers", label: "Transfers", to: "/app/transfers", icon: "⇄" },
];

const walletMenuOpen = ref(false);
const walletControlRef = ref(null);
const copyAddressState = ref("idle");
let copyAddressTimer = null;

const walletStatusLabel = computed(() => {
  if (props.walletAuthenticated) {
    return "Signed session";
  }
  if (props.walletConnected) {
    return "Wallet connected";
  }
  return "Disconnected";
});

const walletControlTitle = computed(() => {
  if (props.walletAuthenticated) {
    return "Wallet control";
  }
  if (props.walletConnected) {
    return "Sign in to continue";
  }
  return "Connect your wallet";
});

const walletControlSubtitle = computed(() => {
  if (props.walletAuthenticated) {
    return props.helperText;
  }
  if (props.walletConnected) {
    return "Use your signature to unlock agent, market, and run actions.";
  }
  return "Use MetaMask to unlock your operator workspace.";
});

const walletTriggerTitle = computed(() => {
  if (props.walletAuthenticated) {
    return "Wallet ready";
  }
  if (props.walletConnected) {
    return "Sign session";
  }
  return "Connect wallet";
});

const walletTriggerSubtitle = computed(() => {
  if (props.walletAddress) {
    return walletLine.value;
  }
  return "MetaMask required";
});

const walletPrimaryActionLabel = computed(() => {
  if (!props.walletConnected) {
    return "Connect wallet";
  }
  if (!props.walletAuthenticated) {
    return "Sign message";
  }
  return "Refresh workspace";
});

const copyAddressLabel = computed(() => (copyAddressState.value === "done" ? "Copied" : "Copy"));

const walletControlStateClass = computed(() => {
  if (props.walletAuthenticated) {
    return "is-ready";
  }
  if (props.walletConnected) {
    return "is-pending";
  }
  return "is-idle";
});

const walletChainLabel = computed(() => {
  const chainId = `${props.walletChainId || ""}`.toLowerCase();
  if (!chainId) {
    return "Not selected";
  }
  if (chainId === "0x1" || chainId === "1") {
    return "Ethereum Mainnet";
  }
  if (chainId === "0x2105" || chainId === "8453") {
    return "Base";
  }
  if (chainId === "0xa4b1" || chainId === "42161") {
    return "Arbitrum";
  }
  if (chainId === "0x89" || chainId === "137") {
    return "Polygon";
  }
  if (chainId === "0x13882" || chainId === "80002") {
    return "Polygon Amoy";
  }
  if (chainId === "0xaa36a7" || chainId === "11155111") {
    return "Sepolia";
  }
  return props.walletChainId;
});

const walletChainTone = computed(() => {
  const label = walletChainLabel.value.toLowerCase();
  if (label.includes("base")) {
    return "is-base";
  }
  if (label.includes("polygon")) {
    return "is-polygon";
  }
  if (label.includes("arbitrum")) {
    return "is-arbitrum";
  }
  if (label.includes("ethereum")) {
    return "is-ethereum";
  }
  if (label.includes("sepolia")) {
    return "is-sepolia";
  }
  return "is-default";
});

const networkSummary = computed(() => (props.accessSummary === "Wallet ready" ? "Active chain" : "All networks"));
const unitSummary = computed(() => (props.accessSummary === "Wallet ready" ? "Runtime view" : "Session view"));
const walletLine = computed(() => {
  if (props.walletAuthenticated && props.walletAddress) {
    return `${props.walletChainId || "chain"} · ${props.walletAddress.slice(0, 6)}...${props.walletAddress.slice(-4)}`;
  }
  if (!props.walletAddress) {
    return props.accessSummary;
  }
  return `${props.walletChainId || "chain"} · ${props.walletAddress.slice(0, 6)}...${props.walletAddress.slice(-4)}`;
});
const searchPlaceholder = computed(() => {
  if (props.currentSection === "agents") {
    return "Search agents, prompts, or token ids";
  }
  if (props.currentSection === "market") {
    return "Search listings, sellers, or token ids";
  }
  if (props.currentSection === "runs") {
    return "Search runs, outputs, or queue ids";
  }
  return "Search portfolio, wallets, or activity";
});

function isSideActive(item) {
  if (item.section !== props.currentSection) {
    return false;
  }
  if (item.subsection) {
    return props.activeSubsection === item.subsection;
  }
  return true;
}

function toggleWalletMenu() {
  walletMenuOpen.value = !walletMenuOpen.value;
}

function closeWalletMenu() {
  walletMenuOpen.value = false;
}

function handleWalletPrimaryAction() {
  closeWalletMenu();
  if (!props.walletConnected) {
    emit("connect-wallet");
    return;
  }
  if (!props.walletAuthenticated) {
    emit("sign-wallet");
    return;
  }
  emit("refresh");
}

function handleWalletSwitch() {
  closeWalletMenu();
  emit("connect-wallet");
}

function handleRefresh() {
  closeWalletMenu();
  emit("refresh");
}

function handleLogout() {
  closeWalletMenu();
  emit("logout-wallet");
}

async function handleCopyAddress() {
  if (!props.walletAddress) {
    return;
  }
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(props.walletAddress);
    } else {
      const input = document.createElement("textarea");
      input.value = props.walletAddress;
      input.setAttribute("readonly", "");
      input.style.position = "absolute";
      input.style.left = "-9999px";
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      document.body.removeChild(input);
    }
    copyAddressState.value = "done";
    if (copyAddressTimer) {
      clearTimeout(copyAddressTimer);
    }
    copyAddressTimer = setTimeout(() => {
      copyAddressState.value = "idle";
      copyAddressTimer = null;
    }, 1800);
  } catch {
    copyAddressState.value = "idle";
  }
}

function truncateAddress(value, size = 14) {
  if (!value) {
    return "Unavailable";
  }
  if (value.length <= size) {
    return value;
  }
  return `${value.slice(0, Math.max(6, size - 7))}...${value.slice(-4)}`;
}

function handleDocumentPointerDown(event) {
  if (!walletControlRef.value) {
    return;
  }
  if (!walletControlRef.value.contains(event.target)) {
    closeWalletMenu();
  }
}

onMounted(() => {
  document.addEventListener("pointerdown", handleDocumentPointerDown);
});

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", handleDocumentPointerDown);
  if (copyAddressTimer) {
    clearTimeout(copyAddressTimer);
  }
});
</script>
