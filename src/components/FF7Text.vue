<template>
  <component :is="as" class="ff7-text" :class="{ 'ff7-label-cyan': cyan }" :style="style">
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CSSProperties } from "vue";
import "~/styles/ff7-ui.css";

const props = withDefaults(
  defineProps<{
    as?: string;
    /** LV / HP / MP only — everything else in the reference is off-white. */
    cyan?: boolean;
    size?: string | number;
    align?: "left" | "center" | "right";
  }>(),
  { as: "span", cyan: false, size: undefined, align: undefined },
);

const style = computed<CSSProperties>(() => ({
  fontSize:
    props.size === undefined
      ? undefined
      : typeof props.size === "number"
        ? `${props.size}px`
        : props.size,
  textAlign: props.align,
}));
</script>
