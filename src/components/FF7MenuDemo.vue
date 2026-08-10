<template>
  <div ref="stage" class="ff7-stage" :style="{ '--ff7-scale': scale }">
    <div class="ff7-screen">
      <!-- Document order is the z order, and the overlaps are deliberate: the two right-hand
           boxes cover the main panel's right edge, the location box covers its bottom border,
           and the 2px grey connector at x 716..722 is the main panel's own right border
           showing through the y 387..429 gap between them. -->
      <FF7Panel :x="78" :y="29" :width="645" :height="524" />
      <!-- y = -2 because the screen clips the command box's top border; overflow: hidden on
           .ff7-screen is what reproduces that. Its left edge is 668, five pixels right of the
           Time box at 663 — a real misalignment in the original, kept. -->
      <FF7Panel :x="668" :y="-2" :width="204" :height="389" />
      <FF7Panel :x="663" :y="430" :width="209" :height="90" />
      <FF7Panel :x="481" :y="520" :width="391" :height="73" />

      <template v-for="(m, i) in MEMBERS" :key="m.name">
        <FF7Text class="ff7-place" :style="at(292, 63 + OFFSETS[i]!)">{{ m.name }}</FF7Text>

        <FF7Text class="ff7-place" cyan :style="at(292, 97 + OFFSETS[i]!)">LV</FF7Text>
        <FF7Text class="ff7-place" :style="at(332, 97 + OFFSETS[i]!)">{{ m.lv }}</FF7Text>

        <FF7Text class="ff7-place" cyan :style="at(292, 122 + OFFSETS[i]!)">HP</FF7Text>
        <FF7Text class="ff7-place" :style="atRight(494, 122 + OFFSETS[i]!)">{{ m.hp }}</FF7Text>
        <div class="ff7-place ff7-gauge ff7-gauge-hp" :style="gauge(143 + OFFSETS[i]!)" />

        <FF7Text class="ff7-place" cyan :style="at(292, 149 + OFFSETS[i]!)">MP</FF7Text>
        <FF7Text class="ff7-place" :style="atRight(494, 149 + OFFSETS[i]!)">{{ m.mp }}</FF7Text>
        <div class="ff7-place ff7-gauge ff7-gauge-mp" :style="gauge(170 + OFFSETS[i]!)" />

        <FF7Text class="ff7-place" :style="at(484, 88 + OFFSETS[i]!)">next level</FF7Text>
        <div class="ff7-place" :style="at(501, 112 + OFFSETS[i]!)">
          <FF7ProgressBar :value="m.exp" variant="exp" />
        </div>

        <FF7Text class="ff7-place" :style="at(484, 139 + OFFSETS[i]!)">Limit level 1</FF7Text>
        <div class="ff7-place" :style="at(501, 163 + OFFSETS[i]!)">
          <FF7ProgressBar :value="m.limit" variant="limit" />
        </div>
      </template>

      <FF7Text class="ff7-place" :style="at(672, 449)">Time</FF7Text>
      <FF7Text class="ff7-place" :style="atRight(96, 449)">4:52:23</FF7Text>
      <FF7Text class="ff7-place" :style="at(672, 487)">Gil</FF7Text>
      <FF7Text class="ff7-place" :style="atRight(96, 487)">6293</FF7Text>

      <FF7Text class="ff7-place" :style="at(501, 545)">Shinra Bldg.</FF7Text>

      <FF7CommandMenu
        class="ff7-place"
        :style="at(708, MENU_TOP)"
        :items="MENU_ITEMS"
        :selected="0"
        @row-y="(y) => (cursorRowY = y)"
      />

      <FF7HandCursor :x="642" :y="MENU_TOP + cursorRowY + CURSOR_NUDGE" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useTemplateRef } from "vue";
import type { CSSProperties } from "vue";
import FF7Panel from "./FF7Panel.vue";
import FF7Text from "./FF7Text.vue";
import FF7ProgressBar from "./FF7ProgressBar.vue";
import FF7CommandMenu from "./FF7CommandMenu.vue";
import FF7HandCursor from "./FF7HandCursor.vue";
import type { FF7MenuItem } from "./FF7CommandMenu.vue";
import "~/styles/ff7-ui.css";

const SCREEN_WIDTH = 950;

// Every number below is a viewport coordinate off the 950x598 reference crop, so the whole
// screen can be overlaid on the original 1:1 at --ff7-scale: 1.
const MENU_TOP = 19;
// The cursor's sprite box starts 3px above the row's cap top (row 19, sprite 22).
const CURSOR_NUDGE = 3;
// Party rows repeat every 148.5px; these are the rounded per-member offsets that keep all
// four columns (name, stats, labels, bars) within a pixel of the reference.
const OFFSETS = [0, 149, 297];

const MENU_ITEMS: FF7MenuItem[] = [
  "Item",
  "Magic",
  "Materia",
  "Equip",
  "Status",
  "Order",
  "Limit",
  "Config",
  null,
  "Save",
  "Quit",
];

// Strings are transcribed verbatim, spacing included: the original pads "465/ 465" so the two
// figures line up under each other, and correcting it would be correcting the game.
const MEMBERS = [
  { name: "Cloud", lv: "13", hp: "465/ 465", mp: "105/ 105", exp: 0.699, limit: 0.867 },
  { name: "Tifa", lv: "12", hp: "429/ 429", mp: "87/ 87", exp: 0.531, limit: 0.378 },
  { name: "Barret", lv: "12", hp: "477/ 477", mp: "80/ 80", exp: 0.322, limit: 0.972 },
];

const at = (x: number, y: number): CSSProperties => ({ left: `${x}px`, top: `${y}px` });
const atRight = (right: number, y: number): CSSProperties => ({
  right: `${right}px`,
  top: `${y}px`,
});
const gauge = (y: number): CSSProperties => ({ left: "330px", top: `${y}px`, width: "129px" });

const cursorRowY = ref(0);

const stage = useTemplateRef<HTMLElement>("stage");
// Capped at 1 so the reference resolution is a ceiling, not a target: upscaling a pixel
// replica past its own grid is the one thing that would make it look wrong.
const scale = ref(1);
let observer: ResizeObserver | undefined;

onMounted(() => {
  const el = stage.value;
  if (!el) return;
  observer = new ResizeObserver(([entry]) => {
    const width = entry?.contentRect.width ?? SCREEN_WIDTH;
    scale.value = Math.min(1, width / SCREEN_WIDTH);
  });
  observer.observe(el);
});

onBeforeUnmount(() => observer?.disconnect());
</script>
