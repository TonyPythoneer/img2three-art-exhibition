// The one place that turns an exhibit's asset filenames into real URLs. Everything under
// src/assets/ is hashed by Vite and gets `base` applied for free; public/ would need
// import.meta.env.BASE_URL stitched on by hand at every use site, and the filenames would
// lose their content hash. The gallery card, the hero turntable and the exhibit page all
// come through here, so there is one glob to keep right instead of three.
//
// The patterns stay shallow (`*/`, never `**/`). A `**` would eagerly pull every
// detail-inventory zone crop and PBR map into the client bundle.

const imageUrls = import.meta.glob(["../assets/exhibits/*/*.png", "../assets/exhibits/*/*.webp"], {
  eager: true,
  import: "default",
  query: "?url",
}) as Record<string, string>;

const promptTexts = import.meta.glob("../assets/exhibits/*/*.txt", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

/** "" when the file is not there — a broken `<img>` is easier to spot than a thrown page. */
export const exhibitImageUrl = (assetDir: string, file: string): string =>
  imageUrls[`../assets/exhibits/${assetDir}/${file}`] ?? "";

/** Read at build time and inlined into the prerendered HTML, so the `<pre>` ships static.
 *
 *  ponytail: prompts come from src/assets/exhibits/ only. There used to be a second glob
 *  over repo-root `*.md` so a promptFile could be "/SPEC.md" — no exhibit ever used it, and
 *  it shipped CLAUDE.md, AGENTS.md and README.md to every visitor. Bring it back the day an
 *  exhibit's prompt really is a spec file, and scope the glob to that one file. */
export const exhibitPrompt = (assetDir: string, promptFile: string): string =>
  promptTexts[`../assets/exhibits/${assetDir}/${promptFile}`] ?? "";
