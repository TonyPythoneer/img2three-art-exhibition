// Pure data, deliberately free of asset imports and `import.meta.glob`:
// src/utils/exhibitAssets.ts resolves `images` / `promptFile` to real URLs.
//
// This file DOES import `.velite/index.js` below to merge velite-managed copy onto the
// ff7-cloud-strife-ultima-weapon entry. That is safe for this file's importers (page components) but
// it means this file must NOT be imported by vite.config.ts: vite.config.ts's import graph is
// watched by vite-plus, and a change to a file it transitively touches (here, the
// velite-generated `.velite/index.js`, rewritten on every content edit) forces a full config
// reload that races velite's delete-then-write into a crash loop. So vite.config.ts reads the
// route-slug list from src/utils/exhibitSlugs.ts instead, which never touches `.velite`.

export type ExhibitStatus = "planning" | "building" | "done";

export type Exhibit = {
  slug: string;
  title: string;
  subtitle: string;
  status: ExhibitStatus;
  /** Where the reference art came from. */
  source: string;
  /** Filenames inside src/assets/exhibits/<assetDir ?? slug>/. */
  images: { file: string; caption: string }[];
  /** Plain-text prompt inside src/assets/exhibits/<assetDir ?? slug>/, rendered verbatim
   *  on the page. */
  promptFile: string;
  /** Folder under src/assets/exhibits/ holding images/promptFile, and under
   *  artifacts/exhibits/ holding the gate evidence, when it differs from the public route
   *  `slug` (e.g. the route was renamed but the exhibit folder and gate scripts were not). */
  assetDir?: string;
  /** Gate evidence linked rather than rendered — it lives in artifacts/exhibits/<assetDir>/,
   *  outside the bundle. A leading "/" links from the repo root instead. */
  docs?: { file: string; label: string }[];
  /** Set when the exhibit ships a live procedural model. The page mounts the
   *  viewer client side only; three.js must never run during static generation. */
  liveModel?: boolean;
  /** Build version of the img2three.js sculpt that produced this model, shown on
   *  the badge shared with the gallery card. */
  modelVersion?: string;
  /** YouTube video ID for the background-music bar. Only exhibits listed here show it. */
  audioVideoId?: string;
  /** Song title shown in the audio bar's info panel. */
  audioTitle?: string;
};

// Velite-managed copy. This import makes `.velite/index.js` part of this file's module graph,
// which is why vite.config.ts must NOT import this file (see the header comment). The velite
// schema mirrors the fields here: slug/title/subtitle/source/images/audioVideoId/audioTitle.
import veliteExhibits from "../../.velite/exhibits.json" with { type: "json" };

const veliteBySlug = new Map(veliteExhibits.map((e) => [e.slug, e]));

// Fields sourced from velite for a given slug. Slug/status/liveModel/promptFile/docs stay inline.
function veliteFields(
  slug: string,
): Pick<Exhibit, "title" | "subtitle" | "source" | "images" | "audioVideoId" | "audioTitle"> {
  const v = veliteBySlug.get(slug);
  if (!v) throw new Error(`velite: no copy for exhibit "${slug}"`);
  return {
    title: v.title,
    subtitle: v.subtitle,
    source: v.source,
    images: v.images,
    audioVideoId: v.audioVideoId,
    audioTitle: v.audioTitle,
  };
}

export const exhibits: Exhibit[] = [
  {
    slug: "ff7-cloud-strife-ultima-weapon",
    status: "done",
    liveModel: true,
    modelVersion: "img2three.js v1.4",
    promptFile: "prompt.txt",
    ...veliteFields("ff7-cloud-strife-ultima-weapon"),
  },
  {
    slug: "ff7-cloud-strife-polygon-figure",
    status: "building",
    // Head-bare mounted (skull, neck, choker). Hair, eyes, ears pending.
    liveModel: true,
    promptFile: "prompt.txt",
    ...veliteFields("ff7-cloud-strife-polygon-figure"),
  },
];

export const exhibitBySlug = (slug: string): Exhibit | undefined =>
  exhibits.find((e) => e.slug === slug);
