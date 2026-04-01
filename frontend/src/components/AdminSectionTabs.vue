<template>
  <section class="section-tabs">
    <div class="section-tabs-copy">
      <p class="section-label">Section Pages</p>
      <strong>{{ sectionLabel }}</strong>
    </div>
    <nav class="section-tabs-nav" aria-label="Secondary">
      <RouterLink
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="section-tab"
        :class="{ 'is-active': activeSubsection === item.id }"
      >
        {{ item.label }}
      </RouterLink>
    </nav>
  </section>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    required: true,
  },
  sectionLabel: {
    type: String,
    required: true,
  },
  activeSubsection: {
    type: String,
    default: null,
  },
});
</script>
