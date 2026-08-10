import type { ExhibitStatus } from "./index.js";

/** The status pill's label, shared by the gallery card and the exhibit summary
 *  so the same exhibit never reads "Building" in one place and "building" in the other. */
export const STATUS_LABELS: Record<ExhibitStatus, string> = {
  planning: "Planning",
  building: "Building",
  done: "Done",
};
