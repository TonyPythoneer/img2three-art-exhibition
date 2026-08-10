<template>
  <figure v-for="image in images" :key="image.src" class="demo-ref">
    <img class="demo-ref-thumb" :src="image.src" :alt="image.caption" />
    <figcaption>{{ image.caption }}</figcaption>
  </figure>
</template>

<script setup lang="ts">
// Styles: src/styles/showcase/stage-panel.css

defineProps<{ images: { src: string; caption: string }[] }>();
</script>
