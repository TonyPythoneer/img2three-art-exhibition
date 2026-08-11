// Exhibit route slugs. Imported by vite.config.ts (outside the Vite pipeline) to build the
// SSG route list. This module must never transitively import `.velite/*`: vite.config.ts's
// import graph is watched by vite-plus, and a change to a file it transitively touches (such as
// the velite-generated `.velite/index.js`, rewritten on every content edit) forces a full config
// reload that races velite's delete-then-write into a crash loop. So the slugs live here,
// velite-free, and src/exhibits/index.ts consumes `.velite` for client data instead.
// Keep in sync with the `slug` values in src/exhibits/index.ts.
export const exhibitSlugs = ["ff7-cloud-ultima-weapon", "ff7-cloud-strife-figure"];
