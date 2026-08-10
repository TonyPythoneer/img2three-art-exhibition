<template>
  <footer class="footer">
    {{ "Source · " }}
    <a :href="REPO_URL" target="_blank" rel="noopener noreferrer">
      {{ "github.com/TonyPythoneer/img2three-art-exhibition" }}
    </a>
    {{
      " · Reference images copyright Square Enix. This site is for technical documentation and research only."
    }}
  </footer>
</template>

<script setup lang="ts">
import { REPO_URL } from "~/site";

// Styles: src/styles/showcase/home-footer.css
</script>
