import type { Exhibit } from "./index.js";

/**
 * URL of an exhibit's reference image, which lives under `public/exhibits/<assetDir>/`.
 *
 * `public/` files are copied verbatim, so unlike an `import.meta.glob` result they carry
 * neither a content hash nor the site's `base`. This site is a GitHub *project* page served
 * from `/img2three-art-exhibition/`, so the prefix has to go back on by hand — which is
 * exactly the kind of thing three call sites would each get subtly wrong. It lives here once.
 *
 * `assetDir` rather than `slug`: the route a exhibit is served at and the folder its files
 * sit in are allowed to differ, and for the v2 exhibit they do.
 */
export const exhibitAssetUrl = (exhibit: Exhibit, file: string): string =>
  `${import.meta.env.BASE_URL}exhibits/${exhibit.assetDir ?? exhibit.slug}/${file}`;
