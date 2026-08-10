import { ViteSSG } from "vite-ssg";
import { routes } from "vue-router/auto-routes";
import App from "./RootApp.vue";
import "./assets/css/main.css";

// vite-ssg wires @unhead/vue internally, so pages just call useSeoMeta.
export const createApp = ViteSSG(App, {
  routes,
  // vite-ssg passes this straight to createWebHistory. Without it the router is
  // mounted at "/" while the site is served from /img2three-art-exhibition/, so
  // every client side route resolves to zero matches and RouterView renders
  // nothing. The prerendered pages hide it; /render-harness does not.
  base: import.meta.env.BASE_URL,
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return { ...savedPosition, behavior: "instant" };
    if (to.hash) return { el: to.hash, top: 96 };
    return { top: 0, behavior: "instant" };
  },
});
