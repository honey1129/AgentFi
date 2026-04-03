<template>
  <section class="section-tabs">
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
  activeSubsection: {
    type: String,
    default: null,
  },
});
</script>
