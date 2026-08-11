<template>
  <ExhibitStage v-bind="props" :mount="mount" />
</template>

<script setup lang="ts">
import ExhibitStage from "~/components/stage/ExhibitStage.vue";
import type { ExhibitStageProps, StageViewer } from "~/exhibits/partInspector";

/**
 * The exhibit stage before the model exists.
 *
 * ponytail: no three.js here at all. The shell, the brief, the reference plates and
 * the prompt are what wiring this up early buys; an empty WebGL context would add a
 * renderer to dispose and render the same nothing. When Stage 1 ships its parts,
 * replace `mount` with a real `mountCloudStrifeViewer` — nothing else in this file
 * has to move, and the panel picks up the part list on its own.
 */

const props = defineProps<ExhibitStageProps>();

const mount = async (host: HTMLElement): Promise<StageViewer> => {
  const note = document.createElement("p");
  note.className = "stage-placeholder";
  note.textContent = "Model pending — the ten Stage 1 parts are gated behind spec review.";
  host.append(note);
  return {
    parts: [],
    selectPart: () => {},
    setIsolate: () => {},
    dispose: () => note.remove(),
  };
};
</script>
