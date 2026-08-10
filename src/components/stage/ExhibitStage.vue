<template>
  <div class="demo-page">
    <div ref="host" class="demo-canvas-mount"></div>

    <section class="demo-panel">
      <div class="panel-dock-layout">
        <nav class="panel-dock" aria-label="Exhibit navigation">
          <RouterLink
            class="panel-dock-item panel-dock-link"
            to="/"
            aria-label="Back to exhibition list"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M3 12 12 3l9 9M5 10v10h14V10" />
            </svg>
          </RouterLink>
          <span class="panel-dock-divider" aria-hidden="true"></span>

          <button
            v-for="item in dockItems"
            :key="item.id"
            class="panel-dock-item"
            :class="{ 'is-active': activeDock === item.id }"
            type="button"
            :aria-label="item.label"
            :aria-current="activeDock === item.id ? 'location' : undefined"
            @click="activateDock(item.id)"
          >
            <svg v-if="item.id === 'brief'" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="8.5" />
              <path d="M12 10.5v5.5M12 7.5h.01" />
            </svg>
            <svg v-else-if="item.id === 'components'" viewBox="0 0 24 24" aria-hidden="true">
              <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" />
              <path d="m4.5 7.5 7.5 4.2 7.5-4.2M12 11.7V21" />
            </svg>
            <svg v-else-if="item.id === 'controls'" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 6h14M5 12h14M5 18h14" />
              <circle cx="9" cy="6" r="1.8" />
              <circle cx="15" cy="12" r="1.8" />
              <circle cx="11" cy="18" r="1.8" />
            </svg>
            <svg v-else-if="item.id === 'spec'" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 3.5h9l3 3V20.5H6zM15 3.5v3h3M9 11h6M9 15h6" />
            </svg>
            <svg v-else viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 3.5h9l5 5v12H5zM14 3.5v5h5M8.5 13h7M8.5 16.5h7" />
            </svg>
          </button>

          <!-- Exhibit-owned viewer toggles ride the rail so they stay reachable without
               opening a section; pushed to the bottom to keep navigation on top. -->
          <template v-if="$slots['dock-tools']">
            <span class="panel-dock-spacer"></span>
            <span class="panel-dock-divider" aria-hidden="true"></span>
            <slot name="dock-tools" />
          </template>
        </nav>

        <div id="demo-panel-body" class="demo-panel-body">
          <div class="demo-panel-inner">
            <div v-show="activeDock === 'brief'" id="brief" class="panel-dock-section">
              <div class="panel-dock-scroll">
                <ExhibitSummary :exhibit="exhibit" :note="note" />
                <ReferencePlates :images="images" />
              </div>
            </div>

            <div
              v-if="parts.length > 1"
              v-show="activeDock === 'components'"
              id="components"
              class="panel-dock-section"
            >
              <div class="panel-dock-scroll">
                <PanelSectionTitle :exhibit="exhibit" subtitle="Components" />
                <PartInspector
                  :parts="parts"
                  :selected="selected"
                  :isolated="isolated"
                  :isolated-part="isolatedPart"
                  :visible-parts="visibleParts"
                  :provenance="viewer?.provenance"
                  @select="viewer?.selectPart($event)"
                  @isolate="viewer?.setIsolate($event)"
                  @isolate-part="onIsolatePart"
                  @toggle-visible="onToggleVisible"
                  @clear="clearSelection"
                />
              </div>
            </div>

            <div v-show="activeDock === 'controls'" id="controls" class="panel-dock-section">
              <div class="panel-dock-scroll">
                <PanelSectionTitle :exhibit="exhibit" subtitle="Controls" />
                <div class="ff7-settings-body">
                  <!-- One control, so it stays here rather than in a component of its own. -->
                  <div v-if="viewer?.setExplode" class="demo-links">
                    <button
                      class="btn btn-explode"
                      type="button"
                      :class="{ 'is-active': exploded }"
                      :aria-pressed="exploded"
                      @click="toggleExplode"
                    >
                      <span class="explode-glyph">✦</span>
                      <span class="explode-label">{{
                        exploded ? "Assemble" : "Explode parts"
                      }}</span>
                    </button>
                  </div>

                  <!-- Per-exhibit review controls (cameras, lighting, variants, …). -->
                  <div v-if="$slots.controls" class="panel-controls">
                    <slot name="controls" />
                  </div>
                </div>
              </div>
            </div>

            <div v-show="activeDock === 'spec'" id="spec" class="panel-dock-section">
              <div class="panel-dock-scroll">
                <PanelSectionTitle :exhibit="exhibit" subtitle="Spec" />
                <PromptDisclosure :prompt="prompt" />
              </div>
            </div>

            <div
              v-if="exhibit.docs?.length"
              v-show="activeDock === 'docs'"
              id="docs"
              class="panel-dock-section"
            >
              <div class="panel-dock-scroll">
                <PanelSectionTitle :exhibit="exhibit" subtitle="Docs" />
                <ExhibitNotes :docs="exhibit.docs" :doc-href="docHref" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <YoutubeAudioBar
      v-if="exhibit.audioVideoId"
      :video-id="exhibit.audioVideoId"
      :audio-title="exhibit.audioTitle"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, toRefs, watch } from "vue";
import PanelSectionTitle from "./PanelSectionTitle.vue";
import ExhibitSummary from "./ExhibitSummary.vue";
import ReferencePlates from "./ReferencePlates.vue";
import PartInspector from "./PartInspector.vue";
import PromptDisclosure from "./PromptDisclosure.vue";
import ExhibitNotes from "./ExhibitNotes.vue";
import YoutubeAudioBar from "./YoutubeAudioBar.vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import type { ExhibitStageProps, PartInfo, StageViewer } from "~/exhibits/partInspector";

/**
 * The gallery's exhibit page: a full-viewport viewer under a collapsible panel
 * carrying the prompt, the reference plates and the live part inspector. Layout
 * ported from img2threejs-showcase's demo page.
 *
 * This file owns the shell and the viewer's lifecycle only — every block inside
 * the panel is its own component beside this one, in the order they appear on
 * screen. Styles: src/styles/showcase/stage.css (+ stage-panel / stage-parts /
 * stage-responsive).
 *
 * Viewer-agnostic: the exhibit supplies `mount`, and its own controls through the
 * `controls` slot. Three.js only ever loads inside `mount`, which is called on
 * mount, so vite-ssg never evaluates WebGL in node.
 */

const props = defineProps<
  ExhibitStageProps & {
    /** Builds the viewer into `host`. Called again from scratch when `variant` changes. */
    mount: (
      host: HTMLElement,
      onPartChange: (selected: PartInfo | null, isolated: boolean) => void,
    ) => Promise<StageViewer>;
    /** Remounts the viewer whenever this changes — model variants, detail levels. */
    variant?: string;
    isolatedPart?: string | null;
    visibleParts?: Set<string>;
    onIsolatePart?: (name: string) => void;
    onToggleVisible?: (name: string) => void;
  }
>();

const { isolatedPart, visibleParts, onIsolatePart, onToggleVisible } = toRefs(props);

const host = ref<HTMLDivElement | null>(null);
const viewer = shallowRef<StageViewer | null>(null);
const parts = shallowRef<PartInfo[]>([]);
const selected = shallowRef<PartInfo | null>(null);
const isolated = ref(false);
const exploded = ref(false);

const DOCK_ITEMS = [
  { id: "brief", label: "Brief" },
  { id: "components", label: "Components" },
  { id: "controls", label: "Controls" },
  { id: "spec", label: "Spec" },
  { id: "docs", label: "Docs" },
] as const;

// Each dock item's id doubles as its URL hash (#components, #controls, …), so a section is a
// linkable anchor — shareable, and referenceable in conversation without screenshots.
const route = useRoute();
const router = useRouter();
const isDockId = (id: string): id is (typeof DOCK_ITEMS)[number]["id"] =>
  DOCK_ITEMS.some((item) => item.id === id);

const initialHash = route.hash.slice(1);
const activeDock = ref<string>(isDockId(initialHash) ? initialHash : "brief");
const panelVisible = ref(true);
const closing = ref(false);

const dockItems = computed(() =>
  DOCK_ITEMS.filter((item) => item.id !== "docs" || Boolean(props.exhibit.docs?.length)),
);

const activateDock = (id: string) => {
  activeDock.value = id;
  router.replace({ hash: `#${id}` });
};

watch(
  () => route.hash,
  (hash) => {
    const id = hash.slice(1);
    if (isDockId(id) && id !== activeDock.value) activeDock.value = id;
  },
);

const clearSelection = () => {
  viewer.value?.setIsolate(false);
  viewer.value?.selectPart(null);
};

// ponytail: rAF tween instead of a tween library. setExplode just moves parts, and the
// viewer already renders every frame, so interpolating the amount is the whole animation.
const EXPLODE_MS = 1600;
let explodeAmount = 0;
let explodeRaf = 0;

const stopExplodeTween = () => {
  if (explodeRaf) cancelAnimationFrame(explodeRaf);
  explodeRaf = 0;
};

const toggleExplode = () => {
  exploded.value = !exploded.value;
  if (!viewer.value?.setExplode) return;

  stopExplodeTween();
  const from = explodeAmount;
  const to = exploded.value ? 1 : 0;
  const start = performance.now();

  const step = (now: number) => {
    const t = Math.min(1, (now - start) / EXPLODE_MS);
    // easeInOutCubic: slow off the mark, slow into place.
    const eased = t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
    explodeAmount = from + (to - from) * eased;
    viewer.value?.setExplode?.(explodeAmount);
    explodeRaf = t < 1 ? requestAnimationFrame(step) : 0;
  };
  explodeRaf = requestAnimationFrame(step);
};

/** Guards against a slow mount resolving after the variant already moved on. */
let generation = 0;

const build = async () => {
  const token = ++generation;
  viewer.value?.dispose();
  viewer.value = null;
  parts.value = [];
  selected.value = null;
  isolated.value = false;
  exploded.value = false;
  stopExplodeTween();
  explodeAmount = 0;
  if (!host.value) return;

  const built = await props.mount(host.value, (sel, iso) => {
    selected.value = sel;
    isolated.value = iso;
  });
  if (token !== generation) {
    built.dispose();
    return;
  }
  viewer.value = built;
  parts.value = built.parts;
};

onMounted(async () => {
  if (typeof window === "undefined" || !host.value) return;
  await build();
});

watch(() => props.variant, build);

onBeforeUnmount(() => {
  generation++;
  stopExplodeTween();
  viewer.value?.dispose();
});
</script>
