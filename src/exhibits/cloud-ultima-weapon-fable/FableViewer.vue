<template>
  <div class="border-line bg-panel overflow-hidden rounded-lg border">
    <div ref="host" class="relative aspect-4/3 w-full">
      <p
        v-if="!ready"
        class="text-ink-soft absolute inset-0 flex items-center justify-center text-sm"
      >
        Loading 3D viewer
      </p>
    </div>

    <div class="border-line flex flex-wrap gap-x-6 gap-y-3 border-t p-4 text-sm">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-ink-soft">View</span>
        <button
          v-for="p in presets"
          :key="p.id"
          type="button"
          class="chip"
          :class="{ 'chip-on': preset === p.id }"
          @click="setPreset(p.id)"
        >
          {{ p.label }}
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
        <button
          type="button"
          class="chip"
          :class="{ 'chip-on': mode === 'grazing' }"
          @click="setMode('grazing')"
        >
          Grazing check
        </button>
      </div>

      <div class="flex flex-wrap items-center gap-2">
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
          @input="applyExplode()"
        />
        <span class="text-ink-soft w-10 shrink-0 text-right tabular-nums">
          {{ explode.toFixed(2) }}
        </span>
      </label>
      <button type="button" class="chip" @click="resetExplode()">Reset</button>
    </div>

    <div class="border-line flex flex-wrap items-center gap-2 border-t p-4 text-sm">
      <span class="text-ink-soft">Show only</span>
      <button
        v-for="i in isolations"
        :key="i.id"
        type="button"
        class="chip"
        :class="{ 'chip-on': isolation === i.id }"
        @click="setIsolation(i.id)"
      >
        {{ i.label }}
      </button>
    </div>

    <p v-if="stats" class="text-ink-soft border-line border-t p-4 text-sm">
      {{ stats.parts }} named nodes · {{ stats.meshes }} meshes · {{ stats.triangles }} triangles.
      Explode and part isolation both run through
      <code class="bg-panel rounded px-1">root.userData.sculptRuntime</code>, the same contract the
      acceptance gates measure.
    </p>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, shallowRef } from "vue";

// Three.js is imported dynamically inside onMounted. vite-ssg renders this component on the
// server, where there is no WebGL context and no window, so a top-level import would break
// the static build rather than just this widget.

type Preset = "reference" | "front" | "side" | "three-quarter";
type Isolation = "none" | "shell" | "core" | "spine" | "guard" | "handle";
type Mode = "referenceLighting" | "neutralReview" | "grazing";

const presets: { id: Preset; label: string }[] = [
  { id: "reference", label: "Reference" },
  { id: "front", label: "Front" },
  { id: "side", label: "Side" },
  { id: "three-quarter", label: "Three-quarter" },
];

const isolations: { id: Isolation; label: string }[] = [
  { id: "none", label: "All" },
  { id: "shell", label: "Shell" },
  { id: "core", label: "Purple core" },
  { id: "spine", label: "Magenta spines" },
  { id: "guard", label: "Guard" },
  { id: "handle", label: "Handle" },
];

const host = ref<HTMLDivElement | null>(null);
const ready = ref(false);
const preset = ref<Preset>("three-quarter");
const mode = ref<Mode>("referenceLighting");
const isolation = ref<Isolation>("none");
const explode = ref(0);
const spinning = ref(false);
const stats = ref<{ parts: number; meshes: number; triangles: number } | null>(null);

const api = shallowRef<{
  setPreset: (p: Preset) => void;
  setMode: (m: Mode) => void;
  setExplode: (amount: number) => void;
  setIsolation: (t: Isolation) => void;
  setSpinning: (v: boolean) => void;
  dispose: () => void;
} | null>(null);

const setPreset = (value: Preset) => {
  preset.value = value;
  if (value === "reference") spinning.value = false;
  api.value?.setPreset(value);
};
const setMode = (value: Mode) => {
  mode.value = value;
  api.value?.setMode(value);
};
const setIsolation = (value: Isolation) => {
  isolation.value = value;
  api.value?.setIsolation(value);
};
const applyExplode = () => api.value?.setExplode(explode.value);
const resetExplode = () => {
  explode.value = 0;
  api.value?.setExplode(0);
};
const toggleSpin = () => {
  spinning.value = !spinning.value;
  api.value?.setSpinning(spinning.value);
};

onMounted(async () => {
  const element = host.value;
  if (!element) return;
  const { mountFableViewer } = await import("./mountFableViewer");
  const viewer = mountFableViewer(element);
  api.value = viewer;
  stats.value = viewer.stats;
  viewer.setPreset(preset.value);
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
  transition:
    color 0.15s,
    border-color 0.15s;
}

.chip:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
}

/* :hover must be beaten explicitly here — it sets `color` to the accent, which is exactly
   this rule's background, so a hovered selected chip would render its label invisible. */
.chip-on,
.chip-on:hover {
  color: var(--color-ground);
  background: var(--color-accent);
  border-color: var(--color-accent);
}
</style>
