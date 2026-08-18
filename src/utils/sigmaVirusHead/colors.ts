/**
 * Colour codes, sampled from the GREEN palette frame's own pixels — a count over the frame's
 * bbox in `p0-triage.json.greenFrameColours`, never an eye-dropper point. The four palette
 * frames are pixel-identical geometry, so this is the only thing the green frame is authority
 * for, and it is the whole reason this exhibit is the green one.
 */
export const COLORS = {
  /** C1 — every structural edge. 656 px of the frame. */
  wire: "#10D830",
  /** C2 — secondary / far-side edges. 152 px. */
  wireFar: "#10B010",
  /** C3 — both eyes. 57 px. */
  eye: "#E05000",
  /** The sheet's own ground, measured off its corners (`p0-triage.json.measuredBackground`). */
  ground: "#000029",
} as const;

/**
 * Material codes: exactly ONE — a flat emissive wireframe, with no PBR response anywhere on the
 * sheet. Per CLAUDE.md ("count the material codes first; if there are only one or two, fold them
 * into the colour stage") this build has no separate material stage.
 */
export const MATERIAL_CODE_COUNT = 1;
