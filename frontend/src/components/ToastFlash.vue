<template>
  <transition name="fade">
    <div v-if="store.state.flash.visible" class="toast" :class="`toast-${store.state.flash.type}`">
      {{ store.state.flash.message }}
    </div>
  </transition>
</template>

<script setup>
import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();
</script>
