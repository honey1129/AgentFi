<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-mark">{{ brandMark }}</div>
      <div class="sidebar-brand-copy">
        <p class="topbar-kicker">{{ brandKicker }}</p>
        <strong>{{ brandTitle }}</strong>
      </div>
    </div>

    <nav class="sidebar-nav" aria-label="Primary">
      <section v-for="item in navItems" :key="item.section" class="sidebar-group">
        <p class="sidebar-section-label">{{ item.label }}</p>
        <RouterLink
          class="sidebar-link"
          :class="{ 'is-active': currentSection === item.section }"
          :to="item.to"
        >
          <span>{{ item.children?.[0]?.label || item.label }}</span>
        </RouterLink>

        <div v-if="item.children?.length && currentSection === item.section" class="sidebar-children">
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
      <div class="sidebar-card">
        <p class="section-label">Operator</p>
        <strong>{{ operatorSummary }}</strong>
        <p>{{ runtimeSummary }}</p>
      </div>
      <RouterLink v-if="portalTo && portalLabel" :to="portalTo" class="sidebar-switch-link">
        {{ portalLabel }}
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
  operatorSummary: {
    type: String,
    required: true,
  },
  runtimeSummary: {
    type: String,
    required: true,
  },
  brandMark: {
    type: String,
    default: "AF",
  },
  brandKicker: {
    type: String,
    default: "AgentFi Runtime",
  },
  brandTitle: {
    type: String,
    default: "Control Center",
  },
  portalLabel: {
    type: String,
    default: "",
  },
  portalTo: {
    type: String,
    default: "",
  },
});
</script>
