import * as THREE from "three";
import { createSole } from "./createSole";
import { createAnkle } from "./createAnkle";
import { createNeck } from "./createNeck";
import { createWaist } from "./createWaist";
import { createThigh } from "./createThigh";
import { createKnee } from "./createKnee";
import { createCalf } from "./createCalf";
import { createPelvis } from "./createPelvis";

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
  /**
   * The mating name this part's local origin IS — its own upper socket, per §4's socket
   * ledger (§1.4: the origin is the zero vector in the part's own frame). The part ABOVE
   * emits this same name in `userData.sockets`, which is what lets a consumer join two
   * parts without either of them knowing the other's dimensions.
   */
  origin: string;
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
  { name: "soleL", module: "legLeft", origin: "soleTop", build: () => createSole("L") },
  { name: "soleR", module: "legRight", origin: "soleTop", build: () => createSole("R") },
  { name: "ankleL", module: "legLeft", origin: "ankleTop", build: () => createAnkle("L") },
  { name: "ankleR", module: "legRight", origin: "ankleTop", build: () => createAnkle("R") },
  { name: "thighL", module: "legLeft", origin: "hip", build: () => createThigh("L") },
  { name: "thighR", module: "legRight", origin: "hip", build: () => createThigh("R") },
  { name: "kneeL", module: "legLeft", origin: "kneeTop", build: () => createKnee("L") },
  { name: "kneeR", module: "legRight", origin: "kneeTop", build: () => createKnee("R") },
  { name: "calfL", module: "legLeft", origin: "calfTop", build: () => createCalf("L") },
  { name: "calfR", module: "legRight", origin: "calfTop", build: () => createCalf("R") },
  { name: "pelvis", module: "torso", origin: "pelvisTop", build: () => createPelvis() },
  { name: "waist", module: "torso", origin: "waistTop", build: () => createWaist() },
  { name: "neck", module: "head", origin: "neckTop", build: () => createNeck() },
];
