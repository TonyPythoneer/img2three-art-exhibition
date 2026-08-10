<template>
  <div class="ff7-bar" :class="`ff7-bar-${variant}`">
    <div class="ff7-bar-body">
      <div class="ff7-bar-track">
        <div class="ff7-bar-fill" :style="{ width: `${clamped * 100}%` }" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import "~/styles/ff7-ui.css";

const props = withDefaults(
  defineProps<{
    /** 0..1 of the 143px track. */
    value?: number;
    variant?: "exp" | "limit";
  }>(),
  { value: 0, variant: "exp" },
);

const clamped = computed(() => Math.min(1, Math.max(0, props.value)));
</script>
