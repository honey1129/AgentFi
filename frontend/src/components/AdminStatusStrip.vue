<template>
  <section class="status-strip">
    <article v-for="item in statusRows" :key="item.label" class="status-tile">
      <span class="status-tile-label">{{ item.label }}</span>
      <strong class="status-tile-value" :class="`status-${item.tone}`">{{ item.value }}</strong>
      <p>{{ item.detail }}</p>
    </article>
    <article v-for="stat in networkMetrics" :key="stat.label" class="status-tile status-tile-muted">
      <span class="status-tile-label">{{ stat.label }}</span>
      <strong class="status-tile-value">{{ stat.value }}</strong>
      <p>{{ stat.detail }}</p>
    </article>
  </section>
</template>

<script setup>
defineProps({
  statusRows: {
    type: Array,
    required: true,
  },
  networkMetrics: {
    type: Array,
    required: true,
  },
});
</script>
