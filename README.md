# img2three Art Exhibition

A hobby project. I take objects I like, real ones or ones that only exist in a
game, and try to rebuild them as web 3D models, purely for fun.

Each exhibit starts from a single reference image and ends as a procedural
Three.js model: no imported meshes, no downloaded assets, just TypeScript
functions that build the geometry. The site keeps the prompt, the reference
material, and the handful of judgement calls that made or broke each rebuild.
It's a notebook, not a portfolio.

## Stack

Vue 3 + vite-plus + vite-ssg (static prerender) + Tailwind 4, packages via pnpm
catalog, deployed to GitHub Pages.

## Development

```bash
pnpm install
pnpm dev      # http://localhost:3000
pnpm build    # emits dist/
```

## Adding an exhibit

One exhibit is one route is one page directory. Five places, and missing one
means it never shows up on the home page:

1. `src/pages/<slug>/index.vue` — the page itself. Its first line is
   `useExhibit("<slug>")`; the route comes from where the file sits, so there is
   no map to register it in.
2. `src/utils/exhibits.ts` for the entry (`slug`, `assetDir`, `status`,
   `promptFile`, and so on).
3. `src/utils/exhibitSlugs.ts` for the slug. `vite.config.ts` reads this to build
   the prerender list — an allowlist, not a filter, so an unlisted page is simply
   never prerendered.
4. `src/components/home/heroStage.ts` to add it to `heroEntries()`.
5. `content/exhibits/<assetDir>.yml` for the copy velite manages, and
   `src/assets/exhibits/<assetDir>/` for the reference images and `prompt.txt`.

`src/utils/exhibits.ts` is pure data. `src/utils/exhibitAssets.ts` owns the only
`import.meta.glob` over exhibit assets, so the gallery card, the hero turntable
and the exhibit page all resolve URLs the same way.

## Copyright

Reference images belong to their respective rights holders (Final Fantasy VII
material is © Square Enix). They appear here only as documentation of a
procedural reconstruction experiment, non-commercial, with no redistribution
intended.
