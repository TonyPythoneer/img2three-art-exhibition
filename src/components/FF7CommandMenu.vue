<template>
  <div class="ff7-menu" :style="{ '--ff7-menu-pitch': `${PITCH}px`, '--ff7-menu-gap': `${GAP}px` }">
    <template v-for="(item, i) in items" :key="i">
      <div v-if="item === null" class="ff7-menu-gap" />
      <div v-else class="ff7-menu-row">
        <FF7Text>{{ item }}</FF7Text>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import FF7Text from "./FF7Text.vue";
import "~/styles/ff7-ui.css";

/** `null` is the blank row between Config and Save. */
export type FF7MenuItem = string | null;

const PITCH = 32;
// Config's cap top is 243 and Save's is 309 — one row plus 34, not 32. The original screen is
// uneven here, and the blank row is where the extra 2px live.
const GAP = 34;

const props = withDefaults(
  defineProps<{
    items: FF7MenuItem[];
    /** Index into `items`; a `null` row is not selectable. */
    selected?: number;
  }>(),
  { selected: 0 },
);

const emit = defineEmits<{ "row-y": [y: number] }>();

// Distance from the menu's own top (= the first row's cap top) to the selected row's cap top,
// so the caller can hang the hand cursor off it instead of hard-coding a second y.
const selectedRowY = computed(() =>
  props.items
    .slice(0, Math.max(0, props.selected))
    .reduce((y, item) => y + (item === null ? GAP : PITCH), 0),
);

watch(selectedRowY, (y) => emit("row-y", y), { immediate: true });

defineExpose({ selectedRowY });
</script>
