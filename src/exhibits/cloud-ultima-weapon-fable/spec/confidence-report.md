# Confidence Report — inferred and mirrored regions (Fable rebuild)

The reference supplies exactly one view of a low-resolution PS1-era render. Everything
below is a region that view does not resolve; nothing here is presented as measured.
**14 of 47 nodes** are not directly observed (4 mirrored, 10 inferred).

For contrast, the load-bearing MEASURED results this rebuild rests on: blade axis
17.67° (centroid regression R²=0.9994), leaf silhouette symmetric (|L−R| < 1.5 px),
and per-row measurements shear-corrected by local-Y = axis − X·tan(17.67°) — without
the shear term the wing/outline drifts ~0.09–0.14u and IoU stalls at 0.83.

## Corrected conflict — recorded, not silently overwritten

**Rod-fan layout.** The first-round reading called the emitter fan a C2 pinwheel
(rotational symmetry) from a visual read of the guard zoom. Local-coordinate
measurement overturned it: the fans are MIRROR-symmetric and all point tipward —
left 154.8°/134.8° ↔ right 23.7°/41.6°, every rod axis passing through (0, −0.115),
radius band 0.37–0.64. The brief's literal "three mirrored rods per side" was correct;
the earlier misread is retained in `assumptions` as a corrected-conflict record.

## Asymmetry the build keeps

**Left wing is absent.** The reference shows a wing plate only on the right side.
`leftBladeClamp` exists as a small block because the brief mandates the node, at
confidence 0.40 — but the right wing is deliberately NOT mirrored onto the left.
Mirroring it would contradict the only view we have.

## Non-visible nodes

| Node | Type | Conf. | Why |
|---|---|---|---|
| `outerShellBack` | mirrored | 0.60 | back face mirrors front (single view) |
| `purpleCoreBack` | mirrored | 0.60 | back face mirrors front |
| `spineBack` | mirrored | 0.55 | back face mirrors front |
| `goldCenterCollarBack` | mirrored | 0.45 | collar back mirrors front |
| `outerShellTip` | inferred | 0.50 | tip extends to Y=2.82 by taper continuation (frame-cropped) |
| `leftEmitterUpper` | inferred | 0.50 | fan continuation; partially occluded by blade base |
| `blackGripSleeve` | inferred | 0.50 | grip mostly cropped from frame |
| `spineBaseSocket` | inferred | 0.50 | junction hidden behind guard hub |
| `upperBladeCollar` | inferred | 0.55 | mount region occluded by shell base |
| `rightEmitterUpper` | inferred | 0.45 | fan continuation past guard silhouette |
| `internalTang` | inferred | 0.40 | mechanically implied, never visible |
| `leftBladeClamp` | inferred | 0.40 | brief-mandated node; no left wing visible (see above) |
| `pommelCollar` | inferred | 0.40 | below frame crop, brief-mandated |
| `goldPommelTip` | inferred | 0.40 | below frame crop, brief-mandated |

## Frame-cropped assumptions

- Tip beyond the frame: taper continuation to Y=2.82, confidence 0.5.
- Pommel region below Y=−0.52 built from the brief, not the image, confidence 0.4.
- Blade total thickness 0.06u — no side view exists, confidence 0.5.

A second view (left side or back) would settle every row above; none contradicts the
single available view except where explicitly recorded.
