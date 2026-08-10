<template>
  <div class="ff7-panel" :style="style"><slot /></div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CSSProperties } from "vue";
import "~/styles/ff7-ui.css";

/** Coordinates are the reference screen's own pixels, measured to the outermost border row. */
const props = defineProps<{
  x?: number;
  y?: number;
  width?: number;
  height?: number;
}>();

// The reference field is bilinear inside each box — every panel runs the whole ramp from its
// own top-left to its own bottom-right — and it falls off faster across the width than down
// the height, 0.67 to 0.33 by least squares over 22 samples. A CSS angle is measured in screen
// space, so the angle that reproduces that depends on the box's aspect: the tall command menu
// needs 104deg where the near-square status panel needs 121deg. Without both dimensions there
// is nothing to solve for and the gradient falls back to the plain corner keyword.
const WIDTH_BIAS = 0.67;
const angle = computed(() => {
  const { width, height } = props;
  if (width === undefined || height === undefined) return undefined;
  const fromVertical = Math.atan2(WIDTH_BIAS / width, (1 - WIDTH_BIAS) / height);
  return `${(180 - (fromVertical * 180) / Math.PI).toFixed(2)}deg`;
});

// Absolute placement is opt-in. Without coordinates the panel stays a flow element, which is
// what makes the frame reusable on pages that are not the 950x598 reference stage.
const style = computed<CSSProperties>(() => ({
  position: props.x === undefined && props.y === undefined ? undefined : "absolute",
  left: props.x === undefined ? undefined : `${props.x}px`,
  top: props.y === undefined ? undefined : `${props.y}px`,
  width: props.width === undefined ? undefined : `${props.width}px`,
  height: props.height === undefined ? undefined : `${props.height}px`,
  "--ff7-panel-angle": angle.value,
}));
</script>
