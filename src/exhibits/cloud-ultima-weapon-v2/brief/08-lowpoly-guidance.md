# PS1 Low-Poly Geometry Guidance

This weapon belongs to the PS1 era and must be reconstructed as a precise low-poly object, not as a modern smoothed redesign.

## Source of truth

- Use `references/01-authority-artwork.webp` as the visual authority.
- Use `assets/artwork-sword-crop.webp` for full-color measurement and overlay comparison.
- Use `assets/artwork-sword-transparent.webp` only as a clean subject-isolation aid.
- Derive boundaries from measured artwork landmarks. Do not use a separately invented contour drawing.

## Geometry rules

- Favor a small number of intentional planar faces.
- Use straight silhouette segments or simple faceted transitions where supported by the artwork.
- Keep the model asymmetric when the artwork perspective requires it; do not force symmetry into the validation view.
- The outer white crystal shell has a center ridge and tapers toward sharpened side edges and a crisp tip.
- The inner purple crystal remains a faceted inset volume and is not sharpened like the outer shell.
- Keep the guard, four drivers, grip, and pommel compact and structurally simple.
- Do not add decorative curves, grooves, bevel loops, subdivisions, or surface detail that the artwork does not show.

## Convergence method

1. Measure the authority artwork directly.
2. Record landmarks for the tip, blade edges, inner crystal, gem, guard, four driver endpoints, grip, and pommel.
3. Build the minimum planar geometry needed to connect those landmarks.
4. Render from the artwork-match camera.
5. Compare the render against the artwork crop using silhouette and landmark error.
6. Change geometry only when the measured comparison identifies a mismatch.
