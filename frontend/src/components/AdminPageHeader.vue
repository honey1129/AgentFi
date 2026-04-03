<template>
  <header class="page-header">
    <div class="page-header-copy">
      <p class="page-breadcrumb">{{ breadcrumb }}</p>
      <div class="page-title-row">
        <h1>{{ title }}</h1>
        <span class="page-pill">{{ sectionLabel }}</span>
      </div>
      <p class="page-description">{{ description }}</p>
    </div>

    <div class="page-toolbar">
      <div class="page-meta-row">
        <div class="page-meta-item">
          <span>Access</span>
          <strong>{{ accessSummary }}</strong>
        </div>
        <div class="page-meta-item">
          <span>Runtime</span>
          <strong>{{ helperText }}</strong>
        </div>
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
