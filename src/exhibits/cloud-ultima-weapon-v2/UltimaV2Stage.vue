<template>
  <ExhibitStage
    v-bind="props"
    :mount="mount"
    :isolated-part="isolatedPart"
    :visible-parts="visibleParts"
    :on-isolate-part="handleIsolatePart"
    :on-toggle-visible="handleToggleVisible"
  >
    <template #dock-tools>
      <button
        class="panel-dock-item"
        type="button"
        aria-label="Reset view"
        title="Reset view"
        @click="resetView"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20 12a8 8 0 1 1-2.35-5.66" />
          <path d="M20 4.5V9h-4.5" />
        </svg>
      </button>
      <button
        class="panel-dock-item"
        type="button"
        :class="{ 'is-active': gizmos }"
        :aria-pressed="gizmos"
        :aria-label="gizmos ? 'Hide rotation circles' : 'Show rotation circles'"
        :title="gizmos ? 'Hide rotation circles' : 'Show rotation circles'"
        @click="toggleGizmos"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="8" />
          <ellipse cx="12" cy="12" rx="8" ry="3.2" />
          <ellipse cx="12" cy="12" rx="3.2" ry="8" />
          <path v-if="!gizmos" d="M4 20 20 4" />
        </svg>
      </button>
    </template>

    <template #controls>
      <div class="panel-row">
        <span class="panel-row-label">{{ "View" }}</span>
        <div class="panel-row-options">
          <button
            v-for="p in PRESETS"
            :key="p.id"
            class="chip"
            type="button"
            :class="{ 'chip-on': preset === p.id }"
            @click="setPreset(p.id)"
          >
            {{ p.label }}
          </button>
        </div>
      </div>
      <div class="panel-row">
        <span class="panel-row-label">{{ "Lighting" }}</span>
        <div class="panel-row-options">
          <button
            class="chip"
            type="button"
            :class="{ 'chip-on': lighting === 'referenceLighting' }"
            @click="setLighting('referenceLighting')"
          >
            {{ "Reference Look" }}
          </button>
          <button
            class="chip"
            type="button"
            :class="{ 'chip-on': lighting === 'neutralReview' }"
            @click="setLighting('neutralReview')"
          >
            {{ "Neutral Review" }}
          </button>
          <button
            class="chip"
            type="button"
            :class="{ 'chip-on': lighting === 'blackBox' }"
            @click="setLighting('blackBox')"
          >
            {{ "Black Box Stage" }}
          </button>
          <button class="chip" type="button" :class="{ 'chip-on': spinning }" @click="toggleSpin">
            {{ "Auto Rotate" }}
          </button>
        </div>
      </div>
      <div v-if="lighting === 'blackBox'" class="panel-row">
        <span class="panel-row-label">{{ "Intensity" }}</span>
        <div class="panel-row-options">
          <input
            v-model.number="blackBoxIntensity"
            type="range"
            min="0"
            max="6"
            step="0.05"
            class="panel-slider"
            @input="setBlackBoxIntensity(blackBoxIntensity)"
          />
        </div>
      </div>
    </template>
  </ExhibitStage>
</template>

<script setup lang="ts">
import { ref, shallowRef } from "vue";
import ExhibitStage from "~/components/stage/ExhibitStage.vue";
import type { ExhibitStageProps, PartInfo, StageViewer } from "~/exhibits/partInspector";
// Type-only, so vite-ssg never pulls three.js into the prerender through it.
import type { LightingMode } from "./createUltimaWeaponV2LookDev";

// Everything WebGL is behind the dynamic import inside `mount`, so vite-ssg can prerender
// this component in node.

const props = defineProps<ExhibitStageProps>();

type Preset = "reference" | "front" | "side" | "three-quarter";
// Imported rather than restated. This was a second copy of the union, so adding a mode meant
// editing two files that never referenced each other — miss one and the button type-checks fine
// and does nothing.
type Lighting = LightingMode;

const PRESETS: { id: Preset; label: string }[] = [
  { id: "reference", label: "Reference" },
  { id: "front", label: "Front" },
  { id: "side", label: "Side" },
  { id: "three-quarter", label: "3/4" },
];

type V2Api = StageViewer & {
  setPreset: (p: Preset) => void;
  setMode: (m: Lighting) => void;
  setSpinning: (v: boolean) => void;
  resetView: () => void;
  setGizmosVisible: (v: boolean) => void;
  setBlackBoxIntensity: (v: number) => void;
  toggleableParts: string[];
  setPartVisible: (id: string, visible: boolean) => void;
  selectPart: (name: string | null) => void;
  setIsolate: (on: boolean) => void;
};

const api = shallowRef<V2Api | null>(null);
const preset = ref<Preset>("three-quarter");
// The exhibit page opens on the reference-appearance rig so the render matches the reference
// plate out of the box; the two review rigs stay one click away.
const lighting = ref<Lighting>("referenceLighting");
// A left drag turns the weapon itself, always — no toggle. The stage lights never move, so that
// drag is what sweeps them across the faces; Auto Rotate does the same on its own axis.
const spinning = ref(false);
// Matches the viewer's own default, which the mount below re-asserts.
const gizmos = ref(true);
const blackBoxIntensity = ref(1);
const isolatedPart = ref<string | null>(null);
const visibleParts = ref<Set<string>>(new Set());

const mount = async (
  host: HTMLElement,
  onPartChange: (selected: PartInfo | null, isolated: boolean) => void,
): Promise<StageViewer> => {
  const { mountV2Viewer } = await import("./mountV2Viewer");
  const viewer = mountV2Viewer(host, { onPartChange }) as V2Api;
  api.value = viewer;
  visibleParts.value = new Set(viewer.toggleableParts);
  viewer.setPreset(preset.value);
  viewer.setMode(lighting.value);
  viewer.setSpinning(spinning.value);
  viewer.setGizmosVisible(gizmos.value);
  return viewer;
};

const setPreset = (value: Preset) => {
  preset.value = value;
  // Spinning under the fixed artwork-match camera would defeat the point of that view.
  if (value === "reference") spinning.value = false;
  api.value?.setPreset(value);
};
const setLighting = (value: Lighting) => {
  lighting.value = value;
  api.value?.setMode(value);
  // Switching rebuilds the rig, so the spotlight comes back at its own base intensity. Snap the
  // slider back to 1 to match it — otherwise the control reads whatever it was left at last time
  // while the stage is lit at something else, and every black-box visit starts somewhere
  // different depending on history.
  if (value === "blackBox") blackBoxIntensity.value = 1;
};
const setBlackBoxIntensity = (value: number) => {
  blackBoxIntensity.value = value;
  api.value?.setBlackBoxIntensity(value);
};
const toggleSpin = () => {
  spinning.value = !spinning.value;
  api.value?.setSpinning(spinning.value);
};

// The viewer stops the spin as part of the reset, so the chip has to follow it back off.
const resetView = () => {
  spinning.value = false;
  preset.value = "three-quarter";
  api.value?.resetView();
};

const toggleGizmos = () => {
  gizmos.value = !gizmos.value;
  api.value?.setGizmosVisible(gizmos.value);
};

const handleIsolatePart = (name: string) => {
  const viewer = api.value;
  if (!viewer) return;
  if (isolatedPart.value === name) {
    for (const id of viewer.toggleableParts) viewer.setPartVisible(id, true);
    isolatedPart.value = null;
  } else {
    for (const id of viewer.toggleableParts) viewer.setPartVisible(id, id === name);
    isolatedPart.value = name;
  }
};

const handleToggleVisible = (name: string) => {
  const viewer = api.value;
  if (!viewer) return;
  const next = !visibleParts.value.has(name);
  viewer.setPartVisible(name, next);
  if (next) visibleParts.value.add(name);
  else visibleParts.value.delete(name);
  isolatedPart.value = null;
};
</script>
