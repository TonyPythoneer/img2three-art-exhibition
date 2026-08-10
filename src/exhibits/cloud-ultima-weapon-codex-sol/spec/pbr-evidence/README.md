# PBR evidence decision

The material-evidence route was tested independently on the pale outer-shell crop before applying it to the remaining materials.

- Source crop: `detail-inventory/zone-r0c1.png`, 49×97 pixels.
- `analyze_texture.py` classified the pale dielectric shell as `brushed-steel`, contradicting the visible flat-shaded reference.
- `extract_pbr_evidence.py` reported confidence `0.8`, but its own diagnostics show foreground coverage `0.1262` and low value range.
- The extracted palette includes `#383261`, a purple-core contaminant that is not outer-shell albedo.
- Visual inspection of the generated height, normal, and roughness maps shows the raster staircase silhouette and crop/background boundary encoded as surface relief.

Decision: reject these maps and do not repeat the same contaminated inference for the six smaller or mixed-material crops. Use the observed per-region palettes plus independent procedural roughness and contact AO. The 146×292 source supports color/silhouette evidence, not inverse-rendered physical maps.

Generated evidence remains under `pbr-evidence/outerShellMaterial/` for audit; it is not bound to a runtime material.
