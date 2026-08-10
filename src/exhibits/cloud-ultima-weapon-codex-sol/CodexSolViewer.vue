<template>
  <div class="border-line bg-panel overflow-hidden rounded-lg border">
    <div ref="host" class="relative aspect-4/3 w-full">
      <p
        v-if="!ready"
        class="text-ink-soft absolute inset-0 flex items-center justify-center text-sm"
      >
        Loading Codex Sol 3D viewer
      </p>
    </div>

    <div class="border-line flex flex-wrap gap-x-6 gap-y-3 border-t p-4 text-sm">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-ink-soft">View</span>
        <button
          v-for="item in presets"
          :key="item.id"
          type="button"
          class="chip"
          :class="{ 'chip-on': preset === item.id }"
          @click="setPreset(item.id)"
        >
          {{ item.label }}
        </button>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-ink-soft">Lighting</span>
        <button
          type="button"
          class="chip"
          :class="{ 'chip-on': mode === 'referenceLighting' }"
          @click="setMode('referenceLighting')"
        >
          Reference
        </button>
        <button
          type="button"
          class="chip"
          :class="{ 'chip-on': mode === 'neutralReview' }"
          @click="setMode('neutralReview')"
        >
          Neutral
        </button>
        <button type="button" class="chip" :class="{ 'chip-on': spinning }" @click="toggleSpin()">
          Auto-rotate
        </button>
      </div>
    </div>

    <div class="border-line flex flex-wrap items-center gap-x-6 gap-y-3 border-t p-4 text-sm">
      <label class="flex flex-1 items-center gap-3">
        <span class="text-ink-soft shrink-0">Explode</span>
        <input
          v-model.number="explode"
          type="range"
          min="0"
          max="1"
          step="0.01"
          class="min-w-40 flex-1"
          @input="api?.setExplode(explode)"
        />
        <span class="text-ink-soft w-10 text-right tabular-nums">{{ explode.toFixed(2) }}</span>
      </label>
      <button type="button" class="chip" @click="resetExplode()">Reset</button>
    </div>

    <div class="border-line flex flex-wrap items-center gap-2 border-t p-4 text-sm">
      <span class="text-ink-soft">Show only</span>
      <button
        v-for="item in isolations"
        :key="item.id"
        type="button"
        class="chip"
        :class="{ 'chip-on': isolation === item.id }"
        @click="setIsolation(item.id)"
      >
        {{ item.label }}
      </button>
    </div>

    <p v-if="stats" class="text-ink-soft border-line border-t p-4 text-sm">
      {{ stats.parts }} parts · {{ stats.meshes }} meshes · {{ stats.triangles }} triangles ·
      independent Codex Sol 5.6 xhigh procedural build.
    </p>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, shallowRef } from "vue";
import type { CodexSolIsolation, CodexSolLighting, CodexSolPreset } from "./mountCodexSolViewer";

const presets: { id: CodexSolPreset; label: string }[] = [
  { id: "reference", label: "Reference" },
  { id: "front", label: "Front" },
  { id: "side", label: "Side" },
  { id: "three-quarter", label: "Three-quarter" },
];
const isolations: { id: CodexSolIsolation; label: string }[] = [
  { id: "none", label: "All" },
  { id: "shell", label: "Shell" },
  { id: "core", label: "Purple core" },
  { id: "spine", label: "Magenta spine" },
  { id: "guard", label: "Guard" },
  { id: "handle", label: "Handle" },
];

const host = ref<HTMLDivElement | null>(null);
const ready = ref(false);
const preset = ref<CodexSolPreset>("reference");
const mode = ref<CodexSolLighting>("referenceLighting");
const isolation = ref<CodexSolIsolation>("none");
const explode = ref(0);
const spinning = ref(false);
const stats = ref<{ parts: number; meshes: number; triangles: number } | null>(null);
const api = shallowRef<ReturnType<
  (typeof import("./mountCodexSolViewer"))["mountCodexSolViewer"]
> | null>(null);

const setPreset = (value: CodexSolPreset) => {
  preset.value = value;
  if (value === "reference") spinning.value = false;
  api.value?.setPreset(value);
};
const setMode = (value: CodexSolLighting) => {
  mode.value = value;
  api.value?.setMode(value);
};
const setIsolation = (value: CodexSolIsolation) => {
  isolation.value = value;
  api.value?.setIsolation(value);
};
const resetExplode = () => {
  explode.value = 0;
  api.value?.setExplode(0);
};
const toggleSpin = () => {
  spinning.value = !spinning.value;
  api.value?.setSpinning(spinning.value);
};

onMounted(async () => {
  if (!host.value) return;
  const { mountCodexSolViewer } = await import("./mountCodexSolViewer");
  api.value = mountCodexSolViewer(host.value);
  stats.value = api.value.stats;
  api.value.setPreset(preset.value);
  ready.value = true;
});

onBeforeUnmount(() => api.value?.dispose());
</script>

<style scoped>
.chip {
  border: 1px solid var(--color-line);
  border-radius: 9999px;
  padding: 0.15rem 0.7rem;
  color: var(--color-ink-soft);
}

.chip:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
}

.chip-on,
.chip-on:hover {
  color: var(--color-ground);
  background: var(--color-accent);
  border-color: var(--color-accent);
}
</style>
