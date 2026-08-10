<template>
  <div class="home" :class="{ ready }">
    <div class="aurora" aria-hidden="true"></div>

    <HomeNav />

    <HomeHero :first-slug="exhibits[0]!.slug">
      <template #stage>
        <HeroStage ref="stage" @active="(slug) => (activeSlug = slug)" />
      </template>
    </HomeHero>

    <ExhibitGrid :active-slug="activeSlug" @focus="stage?.focus($event)" />

    <DevTooling v-if="isDev" />

    <HomeFooter />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, useTemplateRef } from "vue";
import { useSeoMeta } from "@unhead/vue";
import HomeNav from "~/components/home/HomeNav.vue";
import HomeHero from "~/components/home/HomeHero.vue";
import HeroStage from "~/components/home/HeroStage.vue";
import ExhibitGrid from "~/components/home/ExhibitGrid.vue";
import HomeFooter from "~/components/home/HomeFooter.vue";
import DevTooling from "~/components/home/DevTooling.vue";
import { exhibits } from "~/exhibits/index.js";

// Styles: src/styles/showcase/home.css (shell + aurora); each block above owns its own.

const stage = useTemplateRef<{ focus: (slug: string) => void }>("stage");
const activeSlug = ref("");
const isDev = import.meta.env.DEV;

// The entrance transitions run off `.ready`, one frame after mount, so they
// animate in rather than being already finished when the page paints.
const ready = ref(false);
onMounted(() => requestAnimationFrame(() => (ready.value = true)));

useSeoMeta({
  title: "img2three Art Exhibition",
  description:
    "A technical exhibit of procedural Three.js models rebuilt from single reference images.",
});
</script>
