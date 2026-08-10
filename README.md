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

Four places, and missing one means it never shows up on the home page:

1. `src/exhibits/<slug>/` for reference images (`*.png`) and `prompt.txt`. They
   must sit directly in the exhibit root; the glob only scans direct children.
2. `src/exhibits/index.ts` for the entry (`slug`, `title`, `images`,
   `promptFile`, `decisions`, and so on). SSG routes are generated from this file.
3. `src/pages/[slug].vue` to register the stage component in the `STAGES` map.
4. `src/components/home/heroStage.ts` to add it to `heroEntries()`.

`src/exhibits/index.ts` is pure data: `vite.config.ts` imports it directly to
generate routes, so keep asset imports and `import.meta.glob` out of it. Pages
resolve image and prompt URLs via glob instead.

## Copyright

Reference images belong to their respective rights holders (Final Fantasy VII
material is © Square Enix). They appear here only as documentation of a
procedural reconstruction experiment, non-commercial, with no redistribution
intended.
