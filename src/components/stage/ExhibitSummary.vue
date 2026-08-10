<template>
  <header class="demo-panel-head">
    <PanelSectionTitle :exhibit="exhibit" subtitle="Brief" />
  </header>

  <div class="demo-meta">
    <div class="badges">
      <span class="badge badge-object">{{ "Live Model" }}</span>
      <span class="badge badge-version">{{ "img2three.js v1.4" }}</span>
      <span class="badge badge-status" :class="`status-${exhibit.status}`">
        {{ STATUS_LABELS[exhibit.status] }}
      </span>
    </div>
    <p>{{ exhibit.source }}</p>
    <p v-if="note">{{ note }}</p>
  </div>
</template>

<script setup lang="ts">
import PanelSectionTitle from "./PanelSectionTitle.vue";
import type { Exhibit } from "~/exhibits/index.js";
import { STATUS_LABELS } from "~/exhibits/status";

// Styles: src/styles/showcase/stage-panel.css

defineProps<{ exhibit: Exhibit; note?: string }>();
</script>
