<template>
  <div class="ff7-menu-preview">
    <div class="ff7-menu-frame">
      <FF7MenuDemo />
    </div>
  </div>
</template>

<script setup lang="ts">
import FF7MenuDemo from "~/components/FF7MenuDemo.vue";

/**
 * Hidden eyeball-verification route for the 1:1 FF7 menu replica (FF7MenuDemo).
 * Not linked from anywhere and deliberately absent from ssgOptions.includedRoutes,
 * so it only exists client-side. Compare by eye against the 950x598 reference
 * capture (artifacts/ff7-ui-reference.png).
 */
</script>

<style scoped>
.ff7-menu-preview {
  min-height: 100vh;
  background: #000;
  display: grid;
  place-items: center;
  padding: 24px;
}

/* 950px is the replica's native grid; the stage letterboxes/downscales itself below that. */
.ff7-menu-frame {
  width: min(100%, 950px);
}
</style>
