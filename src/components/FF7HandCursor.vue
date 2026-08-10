<template>
  <img class="ff7-hand-cursor" :src="src" :style="style" alt="" aria-hidden="true" />
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CSSProperties } from "vue";
import "~/styles/ff7-ui.css";

const props = withDefaults(
  defineProps<{
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  }>(),
  // The sprite occupies x 642..689, y 22..51 in the reference and points right; its fingertip
  // crosses the command box's left border into the blue, which is why it is a sibling of the
  // panel rather than a child.
  { x: undefined, y: undefined, width: 48, height: 30 },
);

// The site is served from /img2three-art-exhibition/, so a hard-coded /assets/... would 404.
const src = `${import.meta.env.BASE_URL}assets/ff7-hand-cursor.png`;

const style = computed<CSSProperties>(() => ({
  position: props.x === undefined && props.y === undefined ? undefined : "absolute",
  left: props.x === undefined ? undefined : `${props.x}px`,
  top: props.y === undefined ? undefined : `${props.y}px`,
  width: `${props.width}px`,
  height: `${props.height}px`,
}));
</script>
