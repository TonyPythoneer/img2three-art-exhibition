<template>
  <component
    :is="stage"
    v-if="exhibit && stage"
    :exhibit="exhibit"
    :prompt="prompt"
    :images="stageImages"
    :doc-href="docHref"
    :note="modelNote"
  />

  <div v-else-if="exhibit" class="mx-auto max-w-5xl px-6 py-16">
    <RouterLink to="/" class="text-ink-soft hover:text-accent text-sm">
      {{ "← Back to Exhibition List" }}
    </RouterLink>

    <h1 class="mt-6 text-3xl font-semibold tracking-tight sm:text-4xl">{{ exhibit.title }}</h1>
    <p class="text-ink-soft mt-3">{{ exhibit.subtitle }}</p>
    <p class="text-ink-soft mt-1 text-sm">{{ "Reference: " }}{{ exhibit.source }}</p>
    <section class="mt-12">
      <h2 class="text-xl font-semibold">{{ "Reference Images" }}</h2>
      <figure v-for="image in exhibit.images" :key="image.file" class="mt-6">
        <img
          :src="imageUrl(image.file)"
          :alt="image.caption"
          class="border-line w-full rounded-lg border"
        />
        <figcaption class="text-ink-soft mt-2 text-sm">{{ image.caption }}</figcaption>
      </figure>
    </section>

    <section v-if="exhibit.docs?.length" class="mt-14">
      <h2 class="text-xl font-semibold">{{ "Documents" }}</h2>
      <p class="text-ink-soft mt-3 text-sm">
        {{
          "Run outputs (masks, camera landmarks, renders, gate results) live in the project root's "
        }}
        <code class="bg-panel rounded px-1">artifacts/</code>
        {{ " directory, not rendered on this page." }}
      </p>
      <ul class="mt-4 space-y-2">
        <li v-for="doc in exhibit.docs" :key="doc.file">
          <a class="text-accent hover:underline" :href="docHref(doc.file)">{{ doc.label }} ↗</a>
        </li>
      </ul>
    </section>

    <section class="mt-14">
      <div class="flex items-baseline justify-between gap-4">
        <h2 class="text-xl font-semibold">Prompt</h2>
        <button class="text-ink-soft hover:text-accent text-sm" type="button" @click="copyPrompt">
          {{ copied ? "Copied" : "Copy" }}
        </button>
      </div>
      <pre class="prompt-block border-line bg-panel mt-4 rounded-lg border p-5">{{ prompt }}</pre>
    </section>
  </div>

  <div v-else class="mx-auto max-w-5xl px-6 py-16">
    <p>Exhibit not found.</p>
    <RouterLink to="/" class="text-accent">Back to exhibition list</RouterLink>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { useSeoMeta } from "@unhead/vue";
import { exhibitBySlug } from "~/exhibits/index.js";
import UltimaV2Stage from "~/exhibits/cloud-ultima-weapon-v2/UltimaV2Stage.vue";

const REPO = "https://github.com/TonyPythoneer/img2three-art-exhibition/blob/main/src/exhibits";
const REPO_ROOT = "https://github.com/TonyPythoneer/img2three-art-exhibition/blob/main";

const imageUrls = import.meta.glob("../exhibits/*/*.png", {
  eager: true,
  import: "default",
  query: "?url",
}) as Record<string, string>;

const promptTexts = import.meta.glob("../exhibits/*/*.txt", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

// Repo-root markdown a promptFile/docs entry can point to via a leading "/"
// (e.g. "/SPEC.md"), for spec files that live outside src/exhibits/<slug>/.
const rootTexts = import.meta.glob("../../*.md", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

// The route name is passed explicitly so the typed router narrows `params` to this
// page's shape. A bare `useRoute()` types `params` as the union of every route.
const route = useRoute("/[slug]");
const slug = computed(() => String(route.params.slug ?? ""));
const exhibit = computed(() => exhibitBySlug(slug.value));

const assetDir = computed(() => exhibit.value?.assetDir ?? slug.value);
const imageUrl = (file: string) => imageUrls[`../exhibits/${assetDir.value}/${file}`] ?? "";
const docHref = (file: string) =>
  file.startsWith("/") ? `${REPO_ROOT}${file}` : `${REPO}/${assetDir.value}/${file}`;
const prompt = computed(() => {
  const found = exhibit.value;
  if (!found) return "";
  if (found.promptFile.startsWith("/")) {
    return rootTexts[`../../${found.promptFile.slice(1)}`] ?? "";
  }
  return promptTexts[`../exhibits/${found.assetDir ?? found.slug}/${found.promptFile}`] ?? "";
});

const MODEL_NOTES: Record<string, string> = {};

const modelNote = computed(() => MODEL_NOTES[slug.value] ?? "");

// Exhibits with a live model get the showcase stage: a full-viewport viewer under a
// panel carrying the prompt, the reference plates and the part inspector. Each entry
// supplies its own viewer and review controls; everything else is shared. An exhibit
// absent from this map falls through to the plain document page below.
const STAGES = {
  "ff7-cloud-ultima-weapon": UltimaV2Stage,
} as Record<string, typeof UltimaV2Stage | undefined>;

const stage = computed(() => STAGES[slug.value]);

const stageImages = computed(() =>
  (exhibit.value?.images ?? []).map((i) => ({ src: imageUrl(i.file), caption: i.caption })),
);

const copied = ref(false);
const copyPrompt = async () => {
  await navigator.clipboard.writeText(prompt.value);
  copied.value = true;
  setTimeout(() => (copied.value = false), 1500);
};

useSeoMeta({
  title: () => (exhibit.value ? `${exhibit.value.title} · img2three` : "img2three"),
  description: () => exhibit.value?.subtitle ?? "",
});
</script>
