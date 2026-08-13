<template>
  <ExhibitStage
    :exhibit="exhibit"
    :prompt="prompt"
    :images="images"
    :doc-href="docHref"
    :mount="mount"
    :variant="variant"
  >
    <template #controls>
      <div class="panel-row">
        <span class="panel-row-label">{{ "Stage" }}</span>
        <div class="panel-row-options">
          <button
            v-for="option in MODES"
            :key="option.id"
            class="chip"
            type="button"
            :class="{ 'chip-on': mode === option.id }"
            :aria-pressed="mode === option.id"
            @click="mode = option.id"
          >
            {{ option.label }}
          </button>
        </div>
      </div>
      <div class="panel-row">
        <span class="panel-row-label">{{ "Built" }}</span>
        <div class="panel-row-options">
          <span class="chip">{{ `${partCount} / 23 Stage 1 parts` }}</span>
        </div>
      </div>
    </template>
  </ExhibitStage>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import ExhibitStage from "~/components/stage/ExhibitStage.vue";
import { useExhibit } from "~/composables/useExhibit.js";
import type { StageViewer } from "~/utils/partInspector";
import { STAGE1_PARTS } from "~/utils/cloudStrifeFigure/parts";

const { exhibit, images, prompt, docHref } = useExhibit("ff7-cloud-strife-polygon-figure");

const MODES = [
  { id: "assembled", label: "Assembled" },
  { id: "gallery", label: "Parts gallery" },
] as const;

const route = useRoute();
const qs = (key: string): string | undefined => {
  const v = route.query[key];
  return typeof v === "string" && v ? v : undefined;
};

// The review harness lives on this route rather than on a page of its own: ?part=<name>
// pins one part, ?view=front|back|left|right|orbit|orbit2 pins an orthographic camera and
// publishes window.__renderReady for headless capture. src/pages/ is the URL surface, and
// one more .vue would be one more junk route.
const mode = ref<(typeof MODES)[number]["id"]>(
  qs("mode") === "assembled" ? "assembled" : "gallery",
);
const partCount = computed(() => STAGE1_PARTS.length);

const opts = computed(() => ({ mode: mode.value, part: qs("part"), view: qs("view") }));
const variant = computed(() =>
  [opts.value.mode, opts.value.part ?? "", opts.value.view ?? ""].join("|"),
);

const mount = async (host: HTMLElement): Promise<StageViewer> => {
  const { mountCloudStrifeViewer } = await import("~/utils/mountCloudStrifeViewer");
  return mountCloudStrifeViewer(host, opts.value);
};
</script>
