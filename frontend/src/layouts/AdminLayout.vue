<template>
  <div class="app-shell" :class="themeClass">
    <div class="admin-layout">
      <AdminSidebar
        :nav-items="navItems"
        :current-section="currentSection"
        :active-subsection="activeSubsection"
      />

      <main class="admin-main">
        <AdminPageHeader
          :breadcrumb="breadcrumb"
          :title="title"
          :section-label="sectionLabel"
          :headline="headline"
          :description="description"
          :access-summary="accessSummary"
          :helper-text="helperText"
          :refreshing="refreshing"
          @refresh="$emit('refresh')"
        />

        <AdminSectionTabs
          v-if="subnavItems.length"
          :items="subnavItems"
          :section-label="sectionLabel"
          :active-subsection="activeSubsection"
        />

        <section class="content-stage">
          <slot />
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import AdminPageHeader from "@/components/AdminPageHeader.vue";
import AdminSectionTabs from "@/components/AdminSectionTabs.vue";
import AdminSidebar from "@/components/AdminSidebar.vue";

defineEmits(["refresh"]);

defineProps({
  themeClass: {
    type: String,
    required: true,
  },
  navItems: {
    type: Array,
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
  breadcrumb: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  sectionLabel: {
    type: String,
    required: true,
  },
  headline: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  accessSummary: {
    type: String,
    required: true,
  },
  helperText: {
    type: String,
    required: true,
  },
  refreshing: {
    type: Boolean,
    default: false,
  },
  subnavItems: {
    type: Array,
    required: true,
  },
});
</script>
