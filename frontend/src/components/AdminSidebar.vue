<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-mark">AF</div>
      <div>
        <p class="topbar-kicker">AgentFi Runtime</p>
        <strong>Admin Console</strong>
      </div>
    </div>

    <nav class="sidebar-nav" aria-label="Primary">
      <section v-for="item in navItems" :key="item.section" class="sidebar-group">
        <RouterLink
          class="sidebar-link"
          :class="{ 'is-active': currentSection === item.section }"
          :to="item.to"
        >
          <span>{{ item.label }}</span>
        </RouterLink>

        <div v-if="item.children?.length" class="sidebar-children">
          <RouterLink
            v-for="child in item.children"
            :key="child.to"
            :to="child.to"
            class="sidebar-sublink"
            :class="{ 'is-active': activeSubsection === child.id }"
          >
            {{ child.label }}
          </RouterLink>
        </div>
      </section>
    </nav>

    <div class="sidebar-foot">
      <RouterLink to="/runtime/overview" class="sidebar-card sidebar-card-link">
        <p class="section-label">System Overview</p>
        <strong>Open runtime snapshot</strong>
        <p>Global health, operator access, chain posture, and registry counts live on the overview page.</p>
      </RouterLink>
    </div>
  </aside>
</template>

<script setup>
defineProps({
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
});
</script>
