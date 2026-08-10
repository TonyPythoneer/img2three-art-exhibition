<template>
  <div class="flex min-h-screen flex-col" :class="{ 'ff7-page': ff7 }">
    <a href="#content" class="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3">
      Skip to content
    </a>

    <main id="content" class="flex-1">
      <RouterView />
    </main>

    <footer v-if="!showcase" class="border-line text-ink-soft border-t px-6 py-8 text-sm">
      <p class="mx-auto max-w-5xl">
        {{
          ff7
            ? "Reference art © Square Enix. This site is a technical record and research showcase of procedural reconstruction."
            : "參考圖版權屬 Square Enix。本站僅作為程序化重建的技術紀錄與研究用途。"
        }}
      </p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterView, useRoute } from "vue-router";
import "~/styles/ff7-page.css";

/** Routes that wear the FF7 menu chrome instead of the gallery's own. Add a path to skin it;
 *  every rule in ff7-page.css is scoped under .ff7-page, so nothing else moves. */
const FF7_ROUTES = ["/ff7-cloud-ultima-weapon"];

/** Routes that bring their own chrome: the landing page has its own nav and footer, and the
 *  exhibit stages are full-viewport viewers a sticky header would cover. */
const SHOWCASE_ROUTES = ["", "/ff7-cloud-ultima-weapon", "/ff7-menu"];

// The class sits on the app shell, not on the page component, because the header and footer
// have to change with it — a page in FF7 blue under an unstyled nav bar reads as a bug.
const route = useRoute();
const path = computed(() => route.path.replace(/\/$/, ""));
const ff7 = computed(() => FF7_ROUTES.includes(path.value));
const showcase = computed(() => SHOWCASE_ROUTES.includes(path.value));
</script>
