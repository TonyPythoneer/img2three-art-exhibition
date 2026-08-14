import * as THREE from "three";
import { COLORS } from "./colors";

/**
 * M-01 matte vinyl — prompt.txt §2's material table: only two material codes exist in the
 * finished model (M-01 and M-02, the printed face), and M-01 covers everything else. All
 * the variation the figure needs lives on the COLOUR axis, so this is ONE set of params
 * (metalness 0, roughness 0.85, flatShading) shared by every M-01 instance below — the same
 * "one shared instance" discipline `MANNEQUIN` used for M-00, just one instance per colour
 * code instead of one for the whole model.
 */
function vinyl(hex: string): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color: hex,
    flatShading: true,
    metalness: 0,
    roughness: 0.85,
  });
}

// Only the codes Stage 1's 23 parts actually use. C-02 (hair), C-06 (straps) and C-09 (the
// printed face) belong to parts that are not built yet — Stage 2/unscheduled — so they stay
// out of this file until the part that needs them exists; an unused material singleton is
// not evidence of anything.
export const MAT_SKIN = vinyl(COLORS["C-01"]);
export const MAT_SHIRT = vinyl(COLORS["C-03"]);
export const MAT_PANTS = vinyl(COLORS["C-04"]);
export const MAT_BELT = vinyl(COLORS["C-05"]);
export const MAT_BOOT = vinyl(COLORS["C-05b"]);
export const MAT_BLACK = vinyl(COLORS["C-07"]);
export const MAT_GREY = vinyl(COLORS["C-08"]);
