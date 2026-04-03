<template>
  <AdminLayout
    :theme-class="'theme-admin'"
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
  title: "Workspace",
  description: "Operate NFT-backed agents through dedicated management workflows.",
  ...(route.meta || {}),
}));

const currentWallet = computed(() => store.state.metamask.wallet);
const currentSection = computed(() => route.meta.section || inferSection(route.path));
const currentSubsection = computed(() => route.meta.subsection || null);
const currentSectionConfig = computed(() => navItems.find((item) => item.section === currentSection.value) || null);
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
const accessSummary = computed(() => (store.authenticated.value ? "Signed session" : "Read only"));

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
