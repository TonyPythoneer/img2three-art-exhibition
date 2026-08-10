<template>
  <header class="demo-panel-head">
    <PanelSectionTitle :exhibit="exhibit" subtitle="Brief" />
  </header>

  <div class="demo-meta">
    <div class="badges">
      <span
        v-for="badge in exhibitBadges(exhibit)"
        :key="badge.class"
        :class="`badge ${badge.class}`"
        >{{ badge.label }}</span
      >
    </div>
    <p>{{ exhibit.source }}</p>
    <p v-if="note">{{ note }}</p>
  </div>
</template>

<script setup lang="ts">
import PanelSectionTitle from "./PanelSectionTitle.vue";
import type { Exhibit } from "~/exhibits/index.js";
import { exhibitBadges } from "~/exhibits/status";

// Styles: src/styles/showcase/stage-panel.css

defineProps<{ exhibit: Exhibit; note?: string }>();
</script>
