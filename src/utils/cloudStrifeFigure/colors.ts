// GENERATED FILE — do not edit.
//
// Source: artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/palette.json
// Writer: artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/emit_colors.py
//
// prompt.txt §2's colour table (C-xx), sampled by clustering, identified by
// position — never by eye-dropper. Every value is the pixel-count weighted mean
// over the four cool orthographic views (front/back/left/right); §2 explains why
// the cool set is adopted over the warm more-angle reference.

/** C-xx -> adopted hex. C-09 (printed face) is a texture, not a flat colour —
 * absent here on purpose; Stage 2's faceDecal owns it. */
export const COLORS = {
  "C-01": "#DBC0B8", // skin (lit)
  "C-01s": "#B7A39D", // skin (mid/shadow)
  "C-02": "#D1B061", // hair yellow
  "C-03": "#4B4873", // shirt purple
  "C-04": "#4D4B7D", // pants purple
  "C-05": "#564C49", // belt olive-brown
  "C-05b": "#403D2F", // boot olive-brown
  "C-06": "#453F3C", // strap brown (UNSCHEDULED part; sampled for reference)
  "C-07": "#252526", // near-black (gloves + pauldron)
  "C-08": "#838587", // bracer grey
} as const;
