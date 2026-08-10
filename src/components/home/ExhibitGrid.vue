<template>
  <section class="gallery">
    <div class="gallery-head">
      <h2>{{ "Exhibits" }}</h2>
      <p>{{ "Every model is generated TypeScript — spin it, read what it was rebuilt from." }}</p>
    </div>
    <div class="grid">
      <RouterLink
        v-for="(exhibit, i) in exhibits"
        :key="exhibit.slug"
        class="card"
        :class="{ active: activeSlug === exhibit.slug }"
        :style="{ '--i': i }"
        :to="`/${exhibit.slug}`"
        @mouseenter="emit('focus', exhibit.slug)"
      >
        <div class="card-media">
          <img
            v-if="cover(exhibit)"
            class="card-thumb"
            :src="cover(exhibit)"
            :alt="`${exhibit.title} reference image`"
            loading="lazy"
          />
          <span class="card-status" :class="`status-${exhibit.status}`">
            {{ STATUS_LABELS[exhibit.status] }}
          </span>
        </div>
        <div class="card-body">
          <div class="card-title">{{ exhibit.title }}</div>
          <div class="card-author">{{ exhibit.subtitle }}</div>
          <div class="badges">
            <span class="badge badge-object">{{
              exhibit.liveModel ? "Live Model" : "Static"
            }}</span>
          </div>
        </div>
      </RouterLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import { exhibits, type Exhibit } from "~/exhibits/index.js";
import { STATUS_LABELS } from "~/exhibits/status";

// Styles: src/styles/showcase/home-gallery.css

defineProps<{ activeSlug: string }>();
const emit = defineEmits<{ focus: [slug: string] }>();

// Eager and hashed by Vite, so `base` is applied for free. public/ would need
// import.meta.env.BASE_URL stitched on by hand at every use site.
const imageUrls = import.meta.glob("../../exhibits/*/*.png", {
  eager: true,
  import: "default",
  query: "?url",
}) as Record<string, string>;

const cover = (exhibit: Exhibit): string | undefined => {
  const first = exhibit.images[0];
  return first ? imageUrls[`../../exhibits/${exhibit.slug}/${first.file}`] : undefined;
};
</script>
