# Artwork Review Checklist

Use this checklist before accepting any assembled model.

## A. Authority and composition

- [ ] The model was compared directly to `assets/artwork-sword-crop.webp` and the authority artwork.
- [ ] The model was authored upright and matched to the artwork through a separate camera/object validation transform.
- [ ] The artwork remains the final authority when secondary references disagree.

## B. BladeGroup

- [ ] Exactly four public blade nodes exist.
- [ ] The pale outer crystal is the largest silhouette and remains visible around the purple insert.
- [ ] The outer blade is narrow near the tip, wider near the root, and faceted rather than rounded.
- [ ] The outer white crystal shell is sharpened: the tip contracts into a crisp point and the left/right sides visibly taper into cutting edges.
- [ ] The purple insert begins with a triangular point and expands into a long tapered trapezoid.
- [ ] The purple insert does not reach the outer blade tip.
- [ ] The purple insert remains an inset crystal mass and is not sharpened into a second knife edge.
- [ ] The dark core is a small, narrow triangle only.
- [ ] The red/magenta root gem is a faceted elongated diamond, not an arrow-shaped flat polygon.
- [ ] Transparent layers do not flicker or disappear due to depth sorting or coplanar faces.

## C. HiltGroup

- [ ] Exactly four hilt part types exist.
- [ ] Exactly four wine-red drivers exist: two left and two right.
- [ ] Drivers are thin and compact; they are not thick boxes or a many-fin fan.
- [ ] Guard side carriers remain small, dark, angled, and end in compact muted-gold caps.
- [ ] No oversized hanging plates appear below the guard.
- [ ] The grip is narrow, dark, and leather-like with restrained wrapping detail.
- [ ] The combined guard and grip read as a T silhouette without adding a fake crossbar.
- [ ] The pommel is a small pointed metallic spinner/cone, not a ball.

## D. Proportion landmarks

Measure after artwork alignment:

| Landmark                         | Requirement                      |
| -------------------------------- | -------------------------------- |
| Outer tip                        | Within 2.5% of image height      |
| Guard center                     | Within 2.5% of image height      |
| Gem center                       | Within 2.5% of image height      |
| Grip end                         | Within 2.5% of image height      |
| Four driver endpoints            | Each within 2.5% of image height |
| Silhouette IoU                   | At least 0.90                    |
| Blade-to-hilt length ratio error | At most 3%                       |

## E. Positive convergence review

- [ ] The outer shell remains a shallow sharpened crystal blade rather than a thick volume.
- [ ] The purple insert remains smaller, centered, inset, and unsharpened.
- [ ] The compact guard and four slim drivers preserve the artwork's visual hierarchy.
- [ ] The root gem, grip, and pommel remain simple dimensional low-poly forms.
- [ ] Every visible line has a clear role in the authority artwork; no decorative geometry was invented.
- [ ] The result reads as a precise PS1-era model rather than a modern smoothed redesign.

## F. Required review renders

- [ ] canonical front orthographic;
- [ ] artwork-match view;
- [ ] side view showing conservative depth;
- [ ] three-quarter view showing crystal facets;
- [ ] transparent-background render;
- [ ] exploded view;
- [ ] 50% overlay on the authority crop;
- [ ] difference or silhouette comparison image.
