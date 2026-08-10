<template>
  <div class="hero-stage">
    <figure v-show="photo" class="stage-input" :class="{ swapping }">
      <img class="stage-photo" :src="photo" alt="Current exhibit reference image" />
      <figcaption>Reference Image</figcaption>
    </figure>
    <div class="stage-beam" aria-hidden="true"></div>
    <div ref="host" class="stage-canvas">
      <span class="stage-badge">{{ badge }}</span>
      <span class="stage-hint">Rebuilt in code</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, shallowRef } from "vue";
import { exhibits } from "~/exhibits/index.js";

// Three.js — and every model factory it pulls in — is loaded inside onMounted.
// vite-ssg prerenders this component in node, where there is no WebGL context.

const emit = defineEmits<{ active: [slug: string] }>();

const imageUrls = import.meta.glob("../../exhibits/*/*.png", {
  eager: true,
  import: "default",
  query: "?url",
}) as Record<string, string>;

const coverOf = (slug: string): string => {
  const file = exhibits.find((e) => e.slug === slug)?.images[0]?.file;
  return file ? (imageUrls[`../../exhibits/${slug}/${file}`] ?? "") : "";
};

const host = ref<HTMLDivElement | null>(null);
const badge = ref("");
const photo = ref("");
const swapping = ref(false);
const stage = shallowRef<{ dispose: () => void; focus: (i: number) => void } | null>(null);
const slugs = shallowRef<string[]>([]);

/** Jump the turntable to an exhibit — what hovering its gallery card does.
 *  Keyed by slug, so the gallery order and the turntable order can drift apart. */
const focus = (slug: string) => {
  const index = slugs.value.indexOf(slug);
  if (index >= 0) stage.value?.focus(index);
};
defineExpose({ focus });

onMounted(async () => {
  if (typeof window === "undefined" || !host.value) return;
  const { HeroStage, heroEntries } = await import("./heroStage");
  const entries = heroEntries();
  slugs.value = entries.map((e) => e.slug);
  const instance = new HeroStage(host.value, entries, (entry) => {
    badge.value = entry.title;
    emit("active", entry.slug);
    // Crossfade rather than cut: the photo and the model are the same claim.
    swapping.value = true;
    window.setTimeout(() => {
      photo.value = coverOf(entry.slug);
      swapping.value = false;
    }, 260);
  });
  instance.start();
  stage.value = instance;
});

onBeforeUnmount(() => stage.value?.dispose());
</script>
