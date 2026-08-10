import type { Exhibit, ExhibitStatus } from "./index.js";

/** The status pill's label, shared by the gallery card and the exhibit summary
 *  so the same exhibit never reads "Building" in one place and "building" in the other. */
export const STATUS_LABELS: Record<ExhibitStatus, string> = {
  planning: "Planning",
  building: "Building",
  done: "Done",
};

export type ExhibitBadge = { class: string; label: string };

/** Badges drawn purely from exhibit data, so the gallery card and the exhibit
 *  page render the same claims for the same model — no hardcoded copy to drift. */
export function exhibitBadges(exhibit: Exhibit): ExhibitBadge[] {
  const badges: ExhibitBadge[] = [
    { class: "badge-object", label: exhibit.liveModel ? "Live Model" : "Static" },
  ];
  if (exhibit.modelVersion) {
    badges.push({ class: "badge-version", label: exhibit.modelVersion });
  }
  badges.push({
    class: `badge-status status-${exhibit.status}`,
    label: STATUS_LABELS[exhibit.status],
  });
  return badges;
}
