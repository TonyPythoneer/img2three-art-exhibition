import { CROSS_SECTION_ROW_STEP, CROSS_SECTIONS } from "./crossSections";
import { halfWidthAt, len, PX } from "./measurements";

/**
 * The head's cross-section at a frame row, in model units — solved from the sprite sheet's own
 * yaw sweep rather than authored.
 *
 * This replaces `chamferedRing(halfWidth, halfWidth * 1.4255, 0.35)`, which asked the reference
 * for one number and invented the other two: a single global depth ratio and a single chamfer,
 * applied to every row as though the head were one shape scaled. The solve says otherwise —
 * depth-over-width runs 0.41 at the crown, 1.40 through the middle and 1.01 at the jaw.
 *
 * Two corrections are applied on top of the solved polygon.
 *
 * **X is renormalised to the front view.** `cross-sections.json.widthValidation` puts the solved
 * width within 2-4% of the measured front width through the body, but at 17-27% on four rows: 0,
 * 44, 64 and 68. Those are where the profile steps hardest — the crown tip, the ear pods' bottom
 * edge, and the jaw's last two rows — and a row grid resampled from 68-70px frames cannot land on
 * a one-row step. The front view measures those rows exactly, so X takes its scale from there and
 * the solve contributes the SHAPE and the DEPTH, which is the part the front view cannot see.
 *
 * **Z is not renormalised**, because nothing independent measures it per row. The one global
 * check that exists — `gate_yaw_sweep.py` — sees the whole model at once and still holds.
 */

const STEP = CROSS_SECTION_ROW_STEP;

type Pt = readonly [number, number];

function lerpSection(py: number): Pt[] | null {
  const i = py / STEP;
  const lo = Math.max(0, Math.min(CROSS_SECTIONS.length - 1, Math.floor(i)));
  const hi = Math.max(0, Math.min(CROSS_SECTIONS.length - 1, Math.ceil(i)));
  const a = CROSS_SECTIONS[lo];
  const b = CROSS_SECTIONS[hi];
  if (!a || !b || a.length === 0 || b.length === 0 || a.length !== b.length) return null;
  const t = hi === lo ? 0 : i - lo;
  const out: Pt[] = [];
  for (let k = 0; k < a.length; k += 1) {
    const pa = a[k];
    const pb = b[k];
    if (!pa || !pb) return null;
    out.push([pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t]);
  }
  return out;
}

/**
 * The solved section at `py`, in model units, with its half-width forced to `halfWidth` (also
 * model units). Returns `null` when the solve left that row under-constrained, so the caller can
 * fall back rather than render a collapsed ring.
 */
export function sectionAt(
  py: number,
  halfWidth = halfWidthAt(py),
): (readonly [number, number])[] | null {
  const sec = lerpSection(py);
  if (!sec) return null;
  let maxAbsX = 0;
  for (const p of sec) maxAbsX = Math.max(maxAbsX, Math.abs(p[0]));
  if (maxAbsX <= 0) return null;
  // The solve works in reference pixels; PX converts, and the x scale is the ratio that lands the
  // section's half-width on the front view's measured one.
  const sx = halfWidth / (maxAbsX * PX);
  return sec.map(([x, z]) => [x * PX * sx, z * PX] as const);
}

/**
 * One global correction on the solved depths.
 *
 * A support-function reconstruction can only ever shrink: every additional measured direction is
 * another half-plane, and none of them can push the body outwards. So the solve under-states, and
 * by a measurable amount. Its widest cross-section has a caliper of 55.3 reference pixels, while
 * the widest frame in the vetted pure-yaw set measures 62 — an independent number that never
 * enters the solve.
 *
 *   62 / 55.3 = 1.1212
 *
 * `gate_yaw_sweep.py` is what holds it honest: it compares the model's own width sweep against
 * the reference's, so an over- or under-correction here shows up there immediately.
 */
const SOLVE_UNDERSHOOT = 1.1212;

/** Half-depth of the solved section at a row, in model units — for the parts that only need z. */
export function halfDepthSolved(py: number): number {
  const sec = lerpSection(py);
  if (!sec) return len(1);
  let maxAbsZ = 0;
  for (const p of sec) maxAbsZ = Math.max(maxAbsZ, Math.abs(p[1]));
  return Math.max(len(0.5), maxAbsZ * PX * SOLVE_UNDERSHOOT);
}
