<template>
  <h2 class="panel-section-title">{{ exhibit.title }}</h2>
  <p v-if="subtitle" class="demo-kicker panel-section-subtitle">{{ subtitle }}</p>
</template>

<script setup lang="ts">
import type { Exhibit } from "~/exhibits/index.js";

// Every panel-dock section repeats this so the exhibit's name stays on screen no matter
// which tab is open, not just Brief. `subtitle` names the current dock tab (Brief,
// Components, …) so it stays legible next to the title. Styles: src/styles/showcase/stage-panel.css.

defineProps<{ exhibit: Exhibit; subtitle?: string }>();
</script>
