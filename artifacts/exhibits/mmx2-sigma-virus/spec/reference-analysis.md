# Fresh P0-P2 reference analysis — Sigma Virus head

## P0 suitability and reference integrity

The authoritative source is `../references/sigma-wireframe-sheet.png`, a wireframe sprite sheet on a
uniform dark background. It is suitable for reconstructing a low-poly head volume and its visible
wireframe surfaces. It is not sufficient evidence for a full Sigma body.

The sheet shows repeated projections and palette variants of one head/helmet structure. The green
palette cell is used for colour authority; geometry comes from the most symmetric full-scale head
crop and the surrounding oblique/yaw views. No texture is projected onto the model.

Uncertainty:

- Camera labels and exact yaw for individual cells are not supplied.
- Original hidden vertex identity and internal topology are not recoverable.
- Rear and underside surfaces are constrained only by oblique views and receive the simplest
  symmetric continuation.

## P1 decomposition and codes

The rebuild uses these independently editable regions. Left/right names are not implementation
mirrors: each side will receive its own measured surface parameters from the frame observations.

1. crown shell / crown plate
2. forehead shell
3. left and right temple shells
4. left and right cheek lobes
5. recessed face cavity
6. left and right eye plates
7. mid-face bridge
8. lower face / jaw
9. left and right chin tabs
10. rear shell continuation

No bilateral or front/back symmetry is assumed. Structural wire uses bright front-facing and dim
far-facing colour codes; eye outlines use the accent colour. Fills remain the reference navy so the
wire is the subject rather than a shaded modern helmet.

## P2 zoom reading

At 6–8x nearest-neighbour inspection, each detected sprite is recorded in
`all-sprite-observations.json`; the stable cross-frame evidence is:

- broad planar crown and side shell, not a sphere;
- the 307 detected sprite observations do not share one fixed left/right silhouette: full-size
  observations reach row-centre asymmetry up to `0.14179` and centroid drift changes sign across
  the sheet; these are retained as geometry evidence rather than averaged away;
- forward forehead plane above a recessed eye region;
- lateral cheek/ear lobes forming the widest silhouette band;
- narrowed jaw and separate lower chin tabs;
- slanted leaf-like eye outlines;
- faceted rear continuation visible in oblique views, but no licensed decorative rear mechanism.

Guess list:

- rear shell: broad symmetric continuation, no invented panels;
- eye depth: recessed geometry, because the eye outline sits inside the face planes;
- chin tabs: independent geometry, because they recur at the same normalized lower-head position;
- exact camera angles: use canonical inspection probes, not false frame labels.

## Acceptance target

The target is not the original source mesh. The target is one editable low-poly head whose front,
30°/60° obliques, side, rear obliques, top, and bottom projections agree with the supplied family.
Silhouette and major planar transitions outrank hidden triangulation.
