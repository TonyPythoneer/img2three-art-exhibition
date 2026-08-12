import { defineConfig, s } from "velite";

// Only ff7-cloud-strife-ultima-weapon has its copy managed here so far; src/exhibits/index.ts
// merges this collection's fields onto the matching entry by `slug`.
export default defineConfig({
  root: "content",
  // `clean: false`: with clean:true, every rebuild deletes .velite/* before rewriting it,
  // opening a window where consumers (vite.config.ts's transitive imports, the dev server's
  // own module graph, `vite-ssg build`'s SSR pass) find the file briefly missing and crash.
  // Content here only grows by adding fields, so leftover stale keys are not a real risk.
  output: { data: ".velite", clean: false },
  collections: {
    exhibits: {
      name: "ExhibitCopy",
      pattern: "exhibits/*.yml",
      schema: s.object({
        slug: s.string(),
        title: s.string(),
        subtitle: s.string(),
        source: s.string(),
        images: s.array(s.object({ file: s.string(), caption: s.string() })),
        audioVideoId: s.string().optional(),
        audioTitle: s.string().optional(),
      }),
    },
  },
});
