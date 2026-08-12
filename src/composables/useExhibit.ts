import { useSeoMeta } from "@unhead/vue";
import { exhibitBySlug } from "~/utils/exhibits.js";
import { exhibitImageUrl, exhibitPrompt } from "~/utils/exhibitAssets.js";

const REPO_ROOT = "https://github.com/TonyPythoneer/img2three-art-exhibition/blob/main";

/**
 * Everything an exhibit page needs, from its own slug.
 *
 * Each exhibit is its own route under src/pages/<slug>/index.vue, so the slug is a
 * literal the page states about itself — nothing is looked up from route params and
 * nothing is reactive. An unregistered slug throws here, which fails the prerender
 * loudly instead of shipping a page that renders "Exhibit not found".
 */
export function useExhibit(slug: string) {
  const exhibit = exhibitBySlug(slug);
  if (!exhibit) throw new Error(`useExhibit: no entry in src/utils/exhibits.ts for "${slug}"`);
  const dir = exhibit.assetDir ?? exhibit.slug;

  const images = exhibit.images.map((image) => ({
    src: exhibitImageUrl(dir, image.file),
    caption: image.caption,
  }));

  // Gate evidence is not in the bundle — it lives in artifacts/exhibits/<assetDir>/ and is
  // linked on GitHub. A leading "/" points at the repo root instead.
  const docHref = (file: string) =>
    file.startsWith("/") ? `${REPO_ROOT}${file}` : `${REPO_ROOT}/artifacts/exhibits/${dir}/${file}`;

  useSeoMeta({ title: `${exhibit.title} · img2three`, description: exhibit.subtitle });

  return { exhibit, images, prompt: exhibitPrompt(dir, exhibit.promptFile), docHref };
}
