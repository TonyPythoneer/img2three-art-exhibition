<template>
  <div class="demo-panel-bar">
    <span class="demo-bar-title">{{ title }}</span>
  </div>
</template>

<script setup lang="ts">
// Styles: src/styles/showcase/stage-panel.css

defineProps<{ title: string }>();
</script>
