import * as THREE from "three";
import { createSole } from "./createSole";
import { createAnkle } from "./createAnkle";

/**
 * The Stage 1 part registry, and the one material every Stage 1 part shares.
 *
 * §1.6 of the model's prompt makes the OBJECT TREE the part table — `partInspector`
 * reads the graph, not a registry — so this list is not an authority on what a part
 * is. It exists for one narrower job: the gallery mode needs to lay parts out side by
 * side BEFORE any assembly exists, and something has to enumerate them.
 *
 * One factory = one part = one entry. Sub-segments inside a factory stay unnamed.
 */

/**
 * M-00 mannequin grey. Stage 1 carries no colour and no material of its own, so every
 * part shares this ONE instance — a `new` per part is waste, and it turns a later
 * material change into a 23-file edit.
 */
export const MANNEQUIN = new THREE.MeshStandardMaterial({
  color: 0xb0b0b0,
  flatShading: true,
  metalness: 0,
  roughness: 0.85,
});

export type PartEntry = {
  /** Exactly the `group.name` the factory sets — §2's part table. */
  name: string;
  /** The group node this part hangs under in the assembly. */
  module: string;
  build: () => THREE.Group;
};

/**
 * Filled one part per turn, in the build order of §4's socket ledger:
 *
 *   sole -> ankle -> calf -> knee -> thigh -> pelvis -> waist -> chest ->
 *   lowerDeltoid -> upperDeltoid -> backArm -> frontArm -> neck -> head
 *
 * A part appears here in the same turn its factory lands, and not before: an entry
 * whose factory does not exist yet would make the gallery lie about what is built.
 *
 * The import cycle with the factories is fine: they only dereference MANNEQUIN inside a
 * function body, which cannot run before this module has finished evaluating.
 */
export const STAGE1_PARTS: PartEntry[] = [
  { name: "soleL", module: "legLeft", build: () => createSole("L") },
  { name: "soleR", module: "legRight", build: () => createSole("R") },
  { name: "ankleL", module: "legLeft", build: () => createAnkle("L") },
  { name: "ankleR", module: "legRight", build: () => createAnkle("R") },
];
