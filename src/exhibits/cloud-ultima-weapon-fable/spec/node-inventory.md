# Node Inventory — Cloud's Ultima Weapon (Fable rebuild)

47 named nodes: 4 macro, 10 meso, 33 micro. Every entry is reachable through `root.userData.sculptRuntime.nodes` and carries `partId`, `category`, `confidence`, `evidenceType`, `assembledTransform` and `explodeVector`.

Evidence types: **visible** measured in the reference (33), **mirrored** bilateral symmetry from a visible counterpart (4), **inferred** no direct evidence (10).

| Node | Level | Material | Evidence | Conf. | Tris | Primitive |
|---|---|---|---|---|---|---|
| `root` | macro | outerBladeShellMaterial | visible | 0.90 |  | box |
| &nbsp;&nbsp;&nbsp;`bladeAssembly` | macro | outerBladeShellMaterial | visible | 0.90 | 556 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`outerBladeShell` | meso | outerBladeShellMaterial | visible | 0.85 | 120 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`outerShellFront` | micro | outerBladeShellMaterial | visible | 0.85 | 36 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`outerShellBack` | micro | outerBladeShellMaterial | mirrored | 0.60 | 36 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`outerShellLeftEdge` | micro | outerBladeShellMaterial | visible | 0.80 | 26 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`outerShellRightEdge` | micro | outerBladeShellMaterial | visible | 0.80 | 20 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`outerShellTip` | micro | outerBladeShellMaterial | inferred | 0.50 | 2 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`purpleEnergyCore` | meso | purpleCoreMaterial | visible | 0.90 | 292 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`purpleCoreFront` | micro | purpleCoreMaterial | visible | 0.85 | 56 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`purpleCoreBack` | micro | purpleCoreMaterial | mirrored | 0.60 | 56 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`purpleCoreEdge` | micro | purpleCoreMaterial | visible | 0.80 | 172 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`purpleCoreTip` | micro | purpleCoreMaterial | visible | 0.85 | 8 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`magentaCentralSpine` | meso | magentaSpineMaterial | visible | 0.80 | 100 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`spineFront` | micro | magentaSpineMaterial | visible | 0.80 | 44 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`spineBack` | micro | magentaSpineMaterial | mirrored | 0.55 | 44 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`spineBaseSocket` | micro | magentaSpineMaterial | inferred | 0.50 | 12 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`bladeMount` | meso | gunmetalGuardMaterial | visible | 0.60 | 44 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`upperBladeCollar` | micro | gunmetalGuardMaterial | inferred | 0.55 | 12 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`rightBladeClamp` | micro | outerBladeShellMaterial | visible | 0.75 | 20 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`leftBladeClamp` | micro | outerBladeShellMaterial | inferred | 0.40 | 12 | extrude |
| &nbsp;&nbsp;&nbsp;`guardAssembly` | macro | gunmetalGuardMaterial | visible | 0.85 | 292 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`centralGuardHub` | meso | agedGoldMaterial | visible | 0.80 | 20 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`leftGunmetalShoulder` | meso | gunmetalGuardMaterial | visible | 0.80 | 20 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`rightGunmetalShoulder` | meso | gunmetalGuardMaterial | visible | 0.80 | 20 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`emitterRods` | meso | crimsonEmitterMaterial | visible | 0.80 | 144 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`rightEmitterUpper` | micro | crimsonEmitterMaterial | inferred | 0.45 | 24 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`rightEmitterMiddle` | micro | crimsonEmitterMaterial | visible | 0.85 | 24 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`rightEmitterLower` | micro | crimsonEmitterMaterial | visible | 0.85 | 24 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`leftEmitterUpper` | micro | crimsonEmitterMaterial | inferred | 0.50 | 24 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`leftEmitterMiddle` | micro | crimsonEmitterMaterial | visible | 0.85 | 24 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`leftEmitterLower` | micro | crimsonEmitterMaterial | visible | 0.85 | 24 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`goldGuardParts` | meso | agedGoldMaterial | visible | 0.60 | 56 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`goldCenterCollarFront` | micro | agedGoldMaterial | visible | 0.60 | 16 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`goldCenterCollarBack` | micro | agedGoldMaterial | mirrored | 0.45 | 16 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`goldLowerFinLeft` | micro | agedGoldMaterial | visible | 0.55 | 12 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`goldLowerFinRight` | micro | agedGoldMaterial | visible | 0.55 | 12 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`lowerGuardBlocks` | meso | agedGoldMaterial | visible | 0.75 | 32 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`oliveBlockLeft` | micro | agedGoldMaterial | visible | 0.80 | 16 | extrude |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`oliveBlockRight` | micro | agedGoldMaterial | visible | 0.80 | 16 | extrude |
| &nbsp;&nbsp;&nbsp;`handleAssembly` | macro | gripMaterial | visible | 0.60 | 156 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`internalTang` | micro | gripMaterial | inferred | 0.40 | 12 | box |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`handleNeck` | micro | gripMaterial | visible | 0.70 | 32 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`blackGripCore` | micro | gripMaterial | visible | 0.75 | 32 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`blackGripSleeve` | micro | gripMaterial | inferred | 0.50 | 32 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`pommelCollar` | micro | gunmetalGuardMaterial | inferred | 0.40 | 32 | cylinder |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`goldPommelTip` | micro | agedGoldMaterial | inferred | 0.40 | 16 | cone |
