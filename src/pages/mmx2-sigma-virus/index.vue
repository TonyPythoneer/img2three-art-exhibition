<template>
  <ExhibitStage
    :exhibit="exhibit"
    :prompt="prompt"
    :images="images"
    :doc-href="docHref"
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
          <button class="chip" type="button" :class="{ 'chip-on': spinning }" @click="toggleSpin">
            {{ "Auto Rotate" }}
          </button>
        </div>
      </div>
    </template>
  </ExhibitStage>
</template>

<script setup lang="ts">
import { ref, shallowRef } from "vue";
import ExhibitStage from "~/components/stage/ExhibitStage.vue";
import { useExhibit } from "~/composables/useExhibit.js";
import type { PartInfo, StageViewer } from "~/utils/partInspector";
// Type-only, so vite-ssg never pulls three.js into the prerender through it.
import type { SigmaPreset, SigmaViewerApi } from "~/utils/sigmaVirusHead/mountSigmaVirusViewer";

// Everything WebGL is behind the dynamic import inside `mount`, so vite-ssg can prerender
// this page in node.

const { exhibit, images, prompt, docHref } = useExhibit("mmx2-sigma-virus");

// "Top" earns a preset here that the other exhibits do not give it: the crown-from-above
// frames are the reference's only depth evidence, so this is the view a reader checks guess
// G1 against.
const PRESETS: { id: SigmaPreset; label: string }[] = [
  { id: "front", label: "Front" },
  { id: "three-quarter", label: "3/4" },
  { id: "side", label: "Side" },
  { id: "top", label: "Top" },
];

const api = shallowRef<SigmaViewerApi | null>(null);
const preset = ref<SigmaPreset>("three-quarter");
const spinning = ref(false);
const isolatedPart = ref<string | null>(null);
const visibleParts = ref<Set<string>>(new Set());

const mount = async (
  host: HTMLElement,
  onPartChange: (selected: PartInfo | null, isolated: boolean) => void,
): Promise<StageViewer> => {
  const { mountSigmaVirusViewer } = await import("~/utils/sigmaVirusHead/mountSigmaVirusViewer");
  const viewer = mountSigmaVirusViewer(host, { onPartChange });
  api.value = viewer;
  visibleParts.value = new Set(viewer.toggleableParts);
  viewer.setPreset(preset.value);
  viewer.setSpinning(spinning.value);
  return viewer;
};

const setPreset = (value: SigmaPreset) => {
  preset.value = value;
  spinning.value = false;
  api.value?.setPreset(value);
};

const toggleSpin = () => {
  spinning.value = !spinning.value;
  api.value?.setSpinning(spinning.value);
};

const resetView = () => {
  spinning.value = false;
  preset.value = "three-quarter";
  api.value?.resetView();
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
