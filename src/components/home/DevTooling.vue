<template>
  <section class="dev-tooling">
    <div class="dev-tooling-inner">
      <h2 class="dev-tooling-title">{{ "Dev Tools" }}</h2>
      <nav class="dev-tooling-links">
        <RouterLink class="dev-tooling-link" to="/ff7-menu">
          {{ "FF7 Dashboard" }}
        </RouterLink>
      </nav>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<style scoped>
.dev-tooling {
  border-top: 1px dashed #444;
  margin-top: 3rem;
  padding: 1.5rem 0;
}

.dev-tooling-inner {
  max-width: 72rem;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.dev-tooling-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #888;
  margin: 0 0 0.75rem;
}

.dev-tooling-links {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.dev-tooling-link {
  display: inline-flex;
  align-items: center;
  padding: 0.4rem 0.8rem;
  border: 1px solid #555;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #aaa;
  text-decoration: none;
  transition:
    border-color 0.15s,
    color 0.15s;
}

.dev-tooling-link:hover {
  border-color: #888;
  color: #ddd;
}
</style>
