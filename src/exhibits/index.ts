// Pure data, deliberately free of asset imports and `import.meta.glob`: the page component
// resolves `images` / `promptFile` to real URLs via glob.
//
// This file DOES import `.velite/index.js` below to merge velite-managed copy onto the
// cloud-ultima-weapon-v2 entry. That is safe for this file's importers (page components) but
// it means this file must NOT be imported by vite.config.ts: vite.config.ts's import graph is
// watched by vite-plus, and a change to a file it transitively touches (here, the
// velite-generated `.velite/index.js`, rewritten on every content edit) forces a full config
// reload that races velite's delete-then-write into a crash loop. So vite.config.ts reads the
// route-slug list from src/exhibits/slugs.ts instead, which never touches `.velite`.

export type ExhibitStatus = "planning" | "building" | "done";

export type Exhibit = {
  slug: string;
  title: string;
  subtitle: string;
  status: ExhibitStatus;
  /** Where the reference art came from. */
  source: string;
  /** Filenames inside src/exhibits/<assetDir ?? slug>/. */
  images: { file: string; caption: string }[];
  /** Plain-text prompt inside src/exhibits/<assetDir ?? slug>/, rendered verbatim on the page.
   *  A leading "/" resolves relative to the repo root instead (e.g. "/SPEC.md"). */
  promptFile: string;
  /** Folder under src/exhibits/ holding images/promptFile, when it differs from the public
   *  route `slug` (e.g. the route was renamed but the exhibit folder/gate scripts were not). */
  assetDir?: string;
  /** Markdown living beside the prompt, linked rather than rendered. A leading "/"
   *  links to that path from the repo root instead of src/exhibits/<slug>/. */
  docs?: { file: string; label: string }[];
  /** Set when the exhibit ships a live procedural model. The page mounts the
   *  viewer client side only; three.js must never run during static generation. */
  liveModel?: boolean;
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
    slug: "balamb-garden",
    title: "Balamb Garden",
    subtitle: "Final Fantasy VIII 的中央主建築，程序化 Three.js 重建",
    status: "building",
    liveModel: true,
    source: "FF8 設定集空拍概念圖（671×503 掃描稿）與 Garden 冠冕紋章細節圖",
    images: [
      {
        file: "settei-front-three-quarter.png",
        caption:
          "設定資料「ガーデン・本校舎」，作者 Yusuke Naora 簽名。比空拍圖清楚，且作者註明裝飾類是上漆的浮雕、數量還會再增加。",
      },
      {
        file: "aerial.png",
        caption:
          "主參考圖。中央建築為青瓷灰綠色船體，中央塔樓為淺藍灰底加洛可可壁畫，冠冕懸浮於後上方",
      },
      {
        file: "crown-emblem.png",
        caption: "冠冕紋章細節。銀色巴洛克蕾絲框、四片琥珀嵌板、長短不一的金色光芒",
      },
    ],
    promptFile: "/SPEC.md",
    docs: [
      {
        file: "/SPEC.md",
        label:
          "SPEC.md（單一權威規格，取代 prompt-v1/v2/v3 與四份 amendment；附錄 A 為歷史引用對照，附錄 B 為未決事項）",
      },
    ],
  },
  {
    slug: "ff7-cloud-ultima-weapon",
    assetDir: "cloud-ultima-weapon-v2",
    status: "done",
    liveModel: true,
    promptFile: "prompt.txt",
    ...veliteFields("cloud-ultima-weapon-v2"),
  },
];

export const exhibitBySlug = (slug: string): Exhibit | undefined =>
  exhibits.find((e) => e.slug === slug);
