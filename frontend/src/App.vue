<template>
  <UserLayout
    v-if="isUserView"
    :theme-class="themeClass"
    :nav-items="navItems"
    :current-section="currentSection"
    :active-subsection="currentSubsection"
    :title="pageMeta.title"
    :eyebrow="pageMeta.eyebrow || currentSectionConfig?.label || 'Workspace'"
    :headline="pageMeta.headline || pageMeta.description"
    :description="pageMeta.description"
    :access-summary="accessSummary"
    :helper-text="topbarNote"
    :refreshing="store.state.refreshing"
    :subnav-items="subnavItems"
    :brand-mark="brandMark"
    :brand-kicker="brandKicker"
    :brand-title="brandTitle"
    :portal-label="portalLabel"
    :portal-to="portalTo"
    :wallet-connected="Boolean(store.state.metamask.address)"
    :wallet-authenticated="store.authenticated.value"
    :wallet-address="store.state.metamask.address || ''"
    :wallet-chain-id="store.state.metamask.chainId || ''"
    @refresh="store.refreshAll(true)"
    @connect-wallet="store.connectMetaMask(true)"
    @sign-wallet="handleUserSignIn"
    @logout-wallet="store.logoutMetaMask(true)"
  >
    <RouterView />
  </UserLayout>

  <AdminLayout
    v-else
    :theme-class="themeClass"
    :nav-items="navItems"
    :current-section="currentSection"
    :active-subsection="currentSubsection"
    :breadcrumb="breadcrumb"
    :title="pageMeta.title"
    :section-label="currentSectionConfig?.label || 'Workspace'"
    :description="pageMeta.description"
    :access-summary="accessSummary"
    :helper-text="topbarNote"
    :refreshing="store.state.refreshing"
    :subnav-items="subnavItems"
    :brand-mark="brandMark"
    :brand-kicker="brandKicker"
    :brand-title="brandTitle"
    :portal-label="portalLabel"
    :portal-to="portalTo"
    @refresh="store.refreshAll(true)"
  >
    <RouterView />
  </AdminLayout>

  <div>
    <AgentDrawer />
    <ToastFlash />
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";

import AgentDrawer from "@/components/AgentDrawer.vue";
import ToastFlash from "@/components/ToastFlash.vue";
import AdminLayout from "@/layouts/AdminLayout.vue";
import UserLayout from "@/layouts/UserLayout.vue";
import { adminSections, userSections } from "@/navigation";
import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const store = useRuntimeStore();
const audience = computed(() => route.meta.audience || (route.path.startsWith("/app") ? "user" : "admin"));
const isUserView = computed(() => audience.value === "user");
const navItems = computed(() => (isUserView.value ? userSections : adminSections));

const pageMeta = computed(() => ({
  title: isUserView.value ? "Workspace" : "Control Center",
  description: isUserView.value
    ? "Operate your own NFT-backed agents, listings, and runs from a focused operator workspace."
    : "Operate NFT-backed agents through dedicated management workflows.",
  ...(route.meta || {}),
}));

const currentWallet = computed(() => store.state.metamask.wallet);
const currentSection = computed(() => route.meta.section || inferSection(route.path));
const currentSubsection = computed(() => route.meta.subsection || null);
const currentSectionConfig = computed(() => navItems.value.find((item) => item.section === currentSection.value) || null);
const subnavItems = computed(() => currentSectionConfig.value?.children || []);
const currentSubsectionConfig = computed(() => subnavItems.value.find((item) => item.id === currentSubsection.value) || null);

const topbarNote = computed(() => {
  if (store.authenticated.value && currentWallet.value) {
    return currentWallet.value.name || truncateAddress(currentWallet.value.chain_address || currentWallet.value.id);
  }
  if (store.state.metamask.address) {
    return `MetaMask ${truncateAddress(store.state.metamask.address)}`;
  }
  return "Unsigned session";
});

const breadcrumb = computed(() =>
  [currentSectionConfig.value?.label, currentSubsectionConfig.value?.label].filter(Boolean).join(" / ")
);
const accessSummary = computed(() => {
  if (isUserView.value) {
    return store.authenticated.value ? "Wallet ready" : "Connect wallet";
  }
  return store.authenticated.value ? "Signed session" : "Read only";
});
const themeClass = computed(() => (isUserView.value ? "theme-user" : "theme-admin"));
const brandMark = computed(() => (isUserView.value ? "AF" : "AF"));
const brandKicker = computed(() => (isUserView.value ? "Portfolio" : "AgentFi Runtime"));
const brandTitle = computed(() => (isUserView.value ? "AgentFi Wallet" : "Control Center"));
const portalLabel = computed(() => (isUserView.value ? "Open Admin Console" : "Open User Workspace"));
const portalTo = computed(() => (isUserView.value ? "/runtime/overview" : "/app/home"));

function inferSection(path) {
  if (path.startsWith("/app/home")) {
    return "home";
  }
  if (path.startsWith("/app/create")) {
    return "create";
  }
  if (path.startsWith("/app/agents")) {
    return "agents";
  }
  if (path.startsWith("/app/market") || path.startsWith("/app/transfers")) {
    return "market";
  }
  if (path.startsWith("/app/runs")) {
    return "runs";
  }
  if (path.startsWith("/runtime")) {
    return "runtime";
  }
  if (path.startsWith("/launchpad")) {
    return "launchpad";
  }
  if (path.startsWith("/wallets")) {
    return "wallets";
  }
  if (path.startsWith("/agents")) {
    return "agents";
  }
  if (path.startsWith("/market")) {
    return "market";
  }
  if (path.startsWith("/runs")) {
    return "runs";
  }
  return null;
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

async function handleUserSignIn() {
  await store.authenticateMetaMask({
    force: true,
    withRefresh: true,
  });
}

onMounted(async () => {
  await store.initialize();
});
</script>
