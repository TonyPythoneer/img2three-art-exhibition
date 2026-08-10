<template>
  <section class="hero">
    <div class="hero-copy">
      <span class="hero-eyebrow">{{ "A Hobby Project · Procedural Three.js" }}</span>
      <h1 class="hero-title">
        {{ "Things I like," }}<br />
        <span class="grad">{{ "rebuilt in 3D" }}</span
        >{{ " for fun." }}
      </h1>
      <p class="hero-sub">
        {{
          "I take objects from the real world or from games and try to turn them into web 3D models, just because it's fun. Each one starts from a single reference image and ends as procedural Three.js: no imported meshes, only TypeScript that builds the geometry. The prompt, the reference, and the calls that made or broke it are all kept here."
        }}
      </p>
      <div class="cta-row">
        <RouterLink class="btn btn-primary" :to="`/${firstSlug}`">{{ "Enter Exhibit" }}</RouterLink>
        <a class="btn btn-star" :href="REPO_URL" target="_blank" rel="noopener noreferrer">
          {{ "★ Source Code" }}
        </a>
      </div>
      <ol class="pipeline" aria-label="Rebuild pipeline">
        <li><span class="pip-num">01</span>{{ "Reference" }}</li>
        <li class="pip-arrow" aria-hidden="true">→</li>
        <li><span class="pip-num">02</span>{{ "Analysis & Spec" }}</li>
        <li class="pip-arrow" aria-hidden="true">→</li>
        <li><span class="pip-num">03</span>{{ "Procedural Three.js" }}</li>
      </ol>
    </div>

    <!-- The turntable is the second grid column. It arrives as a slot so the page can
         keep a ref to it — hovering a gallery card jumps it to that exhibit. -->
    <slot name="stage" />
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import { REPO_URL } from "~/site";

// Styles: src/styles/showcase/home-hero.css

defineProps<{ firstSlug: string }>();
</script>
