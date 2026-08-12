<template>
  <section class="gallery">
    <div class="gallery-head">
      <h2>{{ "Exhibits" }}</h2>
      <p>{{ "Every model is generated TypeScript. Spin it, read what it was rebuilt from." }}</p>
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
            <span
              v-for="badge in exhibitBadges(exhibit)"
              :key="badge.class"
              :class="`badge ${badge.class}`"
              >{{ badge.label }}</span
            >
          </div>
        </div>
      </RouterLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import { exhibits, type Exhibit } from "~/utils/exhibits.js";
import { exhibitBadges, STATUS_LABELS } from "~/utils/exhibitStatus";
import { exhibitImageUrl } from "~/utils/exhibitAssets.js";

// Styles: src/styles/showcase/home-gallery.css

defineProps<{ activeSlug: string }>();
const emit = defineEmits<{ focus: [slug: string] }>();

const cover = (exhibit: Exhibit): string => {
  const first = exhibit.images[0];
  return first ? exhibitImageUrl(exhibit.assetDir ?? exhibit.slug, first.file) : "";
};
</script>
