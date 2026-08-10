<template>
  <div class="demo-prompt">
    <header class="prompt-header">
      <button
        class="prompt-copy"
        type="button"
        :aria-label="copied ? '已複製' : '複製'"
        @click="copy"
      >
        <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
          <rect
            x="5"
            y="5"
            width="9"
            height="9"
            rx="1"
            fill="none"
            stroke="currentColor"
            stroke-width="1.2"
          />
          <path d="M3 11V3h6" fill="none" stroke="currentColor" stroke-width="1.2" />
        </svg>
      </button>
    </header>
    <pre class="prompt-pre">{{ prompt }}</pre>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

// Styles: src/styles/showcase/stage-panel.css

const props = defineProps<{ prompt: string }>();

const copied = ref(false);
const copy = async () => {
  await navigator.clipboard.writeText(props.prompt);
  copied.value = true;
  setTimeout(() => (copied.value = false), 1500);
};
</script>
