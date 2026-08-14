import * as THREE from "three";
import {
  createUltimaWeaponV2LookDevLights,
  KEY_DIRECTION,
  type LookDevRig,
} from "../ultimaWeaponV2/createUltimaWeaponV2LookDev";

const srgb = (hex: string) => new THREE.Color().setStyle(hex, THREE.SRGBColorSpace);

/**
 * Cloud Strife's own look-dev rig. NOT the same instance as Ultima Weapon's
 * `createUltimaWeaponV2LookDevLights("referenceLighting")` — that rig's light energy (key
 * 0.22 / hemisphere 0.62 / ambient 0.42) was tuned to sum to ~1.0 against a WHITE material
 * whose shading is baked into vertex colour. Cloud Strife's `materials.ts` puts the measured
 * C-xx hex straight into `material.color` with no vertex colour, so borrowing that budget
 * rendered every part at roughly half its authored value — measured directly (median over a
 * >3000px box, front.png): shirt (38,36,63) vs authored (75,72,115) ≈0.51-0.55×, pants
 * ≈0.51-0.56×, skin (128,112,110) vs (219,192,184) ≈0.58-0.60×.
 *
 * Everything except the three light intensities below (environment, background, tone
 * mapping) is unchanged from `referenceLighting` — only the light energy was the bug, so
 * only the light energy moves. The Ultima Weapon rig itself is untouched: it stays the
 * byte-for-byte baseline its own colour/silhouette gates and ΔE records are measured
 * against.
 *
 * The multiplier is ~3.7×, not the ~1.9× a naive "sRGB pixel ratio was ~0.52" reading
 * suggests: `renderer.outputColorSpace` is sRGB, and sRGB-decoding an 8-bit ratio of 0.52
 * back to the *linear* space lighting math actually runs in gives ≈0.28 — a first pass at
 * 1.9× (measured) only brought the linear ratio to ≈0.52, i.e. it moved exactly 1.9× as
 * expected, just from a lower start than the sRGB numbers implied. 1 / 0.28 ≈ 3.7×,
 * confirmed by remeasuring after the first pass instead of assuming it landed.
 */
export function createCloudStrifeLookDevLights(): LookDevRig {
  const base = createUltimaWeaponV2LookDevLights("referenceLighting");

  const lights = new THREE.Group();
  lights.name = "cloudStrifeLookDevRig";

  const key = new THREE.DirectionalLight(0xffffff, 0.81); // 0.22 * ~3.7
  key.position.copy(KEY_DIRECTION).multiplyScalar(12);
  lights.add(key);

  lights.add(new THREE.HemisphereLight(srgb("#EDEDF6"), srgb("#BFC0CC"), 2.27)); // 0.62 * ~3.7
  lights.add(new THREE.AmbientLight(srgb("#DCDCE4"), 1.55)); // 0.42 * ~3.7

  return { ...base, lights };
}
