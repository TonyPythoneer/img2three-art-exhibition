<template>
  <header class="nav">
    <RouterLink class="brand" to="/">
      <span class="brand-name">img2three Art Exhibition</span>
    </RouterLink>
    <div class="nav-actions">
      <a class="nav-star" :href="REPO_URL" target="_blank" rel="noopener noreferrer">
        {{ "★ GitHub" }}
      </a>
    </div>
  </header>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import { REPO_URL } from "~/site";

// Styles: src/styles/showcase/home-nav.css
</script>
