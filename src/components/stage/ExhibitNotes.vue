<template>
  <div v-if="docs?.length" class="demo-links">
    <a
      v-for="doc in docs"
      :key="doc.file"
      class="btn"
      :href="docHref(doc.file)"
      target="_blank"
      rel="noopener noreferrer"
    >
      {{ doc.label }} ↗
    </a>
  </div>
</template>

<script setup lang="ts">
// Styles: src/styles/showcase/stage-panel.css

defineProps<{
  docs?: { file: string; label: string }[];
  docHref: (file: string) => string;
}>();
</script>
