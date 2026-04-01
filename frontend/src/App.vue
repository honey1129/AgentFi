<template>
  <AdminLayout
    :theme-class="appThemeClass"
    :nav-items="navItems"
    :current-section="currentSection"
    :active-subsection="currentSubsection"
    :breadcrumb="breadcrumb"
    :title="pageMeta.title"
    :section-label="currentSectionConfig?.label || 'Workspace'"
    :headline="pageMeta.headline"
    :description="pageMeta.description"
    :access-summary="accessSummary"
    :helper-text="topbarNote"
    :refreshing="store.state.refreshing"
    :subnav-items="subnavItems"
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
import { workspaceSections } from "@/navigation";
import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const store = useRuntimeStore();
const navItems = workspaceSections;

const pageMeta = computed(() => ({
  eyebrow: "AgentFi Runtime",
  title: "Workspace",
  headline: "Operate NFT-backed agents through focused runtime pages.",
  description: "Each route keeps one job in view so wallet auth, ownership, trade, and execution do not collapse into one noisy dashboard.",
  summaryTitle: "Overview",
  summaryBody: "The shell stays shared, but each route keeps a narrower toolset and a clearer page purpose.",
  ...(route.meta || {}),
}));

const currentWallet = computed(() => store.state.metamask.wallet);
const currentSection = computed(() => route.meta.section || inferSection(route.path));
const currentSubsection = computed(() => route.meta.subsection || null);
const appThemeClass = computed(() => `theme-${currentSection.value || "default"}`);
const currentSectionConfig = computed(() => navItems.find((item) => item.section === currentSection.value) || null);
const subnavItems = computed(() => currentSectionConfig.value?.children || []);
const currentSubsectionConfig = computed(() => subnavItems.value.find((item) => item.id === currentSubsection.value) || null);

const topbarNote = computed(() => {
  if (store.authenticated.value && currentWallet.value) {
    return `Signed as ${currentWallet.value.name || truncateAddress(currentWallet.value.chain_address || currentWallet.value.id)}`;
  }
  if (store.state.metamask.address) {
    return `MetaMask connected: ${truncateAddress(store.state.metamask.address)}`;
  }
  return "Connect MetaMask from Launchpad to unlock write actions.";
});

const breadcrumb = computed(() =>
  ["Admin", currentSectionConfig.value?.label, currentSubsectionConfig.value?.label].filter(Boolean).join(" / ")
);
const accessSummary = computed(() => (store.authenticated.value ? "Signed operator can submit writes." : "Read-only until MetaMask sign-in completes."));

function inferSection(path) {
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

onMounted(async () => {
  await store.initialize();
});
</script>
