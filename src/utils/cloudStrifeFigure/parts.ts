import * as THREE from "three";
import { createSole } from "./createSole";
import { createAnkle } from "./createAnkle";
import { createNeck } from "./createNeck";
import { createWaist } from "./createWaist";
import { createThigh } from "./createThigh";
import { createKnee } from "./createKnee";
import { createCalf } from "./createCalf";
import { createPelvis } from "./createPelvis";
import { createChest } from "./createChest";
import { createUpperDeltoid } from "./createUpperDeltoid";
import { createLowerDeltoid } from "./createLowerDeltoid";
import { createBackArm } from "./createBackArm";
import { createFrontArm } from "./createFrontArm";
import { createHead } from "./createHead";

/**
 * The Stage 1 part registry.
 *
 * §1.6 of the model's prompt makes the OBJECT TREE the part table — `partInspector`
 * reads the graph, not a registry — so this list is not an authority on what a part
 * is. It exists for one narrower job: the gallery mode needs to lay parts out side by
 * side BEFORE any assembly exists, and something has to enumerate them.
 *
 * One factory = one part = one entry. Sub-segments inside a factory stay unnamed.
 *
 * Materials: each factory now colours itself from `./materials`'s M-01 singletons (§2's
 * colour table) instead of the M-00 mannequin grey this registry used to hand out — M-00
 * is "the Stage 1 stand-in, gone by Stage 3" (prompt.txt §2), and Stage 3 has landed.
 */

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
  { name: "chest", module: "torso", origin: "chestTop", build: () => createChest() },
  { name: "pelvis", module: "torso", origin: "pelvisTop", build: () => createPelvis() },
  { name: "waist", module: "torso", origin: "waistTop", build: () => createWaist() },
  {
    name: "upperDeltoidL",
    module: "armLeft",
    origin: "shoulder",
    build: () => createUpperDeltoid("L"),
  },
  {
    name: "upperDeltoidR",
    module: "armRight",
    origin: "shoulder",
    build: () => createUpperDeltoid("R"),
  },
  {
    name: "lowerDeltoidL",
    module: "armLeft",
    origin: "deltoidWaist",
    build: () => createLowerDeltoid("L"),
  },
  {
    name: "lowerDeltoidR",
    module: "armRight",
    origin: "deltoidWaist",
    build: () => createLowerDeltoid("R"),
  },
  { name: "backArmL", module: "armLeft", origin: "backArmTop", build: () => createBackArm("L") },
  { name: "backArmR", module: "armRight", origin: "backArmTop", build: () => createBackArm("R") },
  { name: "frontArmL", module: "armLeft", origin: "elbow", build: () => createFrontArm("L") },
  { name: "frontArmR", module: "armRight", origin: "elbow", build: () => createFrontArm("R") },
  { name: "neck", module: "head", origin: "neckTop", build: () => createNeck() },
  { name: "head", module: "head", origin: "skullTop", build: () => createHead() },
];
