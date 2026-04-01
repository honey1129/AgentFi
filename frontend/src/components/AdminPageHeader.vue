<template>
  <header class="page-header">
    <div class="page-header-copy">
      <p class="page-breadcrumb">{{ breadcrumb }}</p>
      <div class="page-title-row">
        <h1>{{ title }}</h1>
        <span class="page-pill">{{ sectionLabel }}</span>
      </div>
      <p class="page-headline">{{ headline }}</p>
      <p class="page-description">{{ description }}</p>
    </div>

    <div class="page-toolbar">
      <div class="toolbar-card">
        <span>Access</span>
        <strong>{{ accessSummary }}</strong>
        <p>{{ helperText }}</p>
      </div>
      <button class="ghost-button" type="button" @click="$emit('refresh')">
        {{ refreshing ? "Refreshing..." : "Refresh Data" }}
      </button>
    </div>
  </header>
</template>

<script setup>
defineEmits(["refresh"]);

defineProps({
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
});
</script>
