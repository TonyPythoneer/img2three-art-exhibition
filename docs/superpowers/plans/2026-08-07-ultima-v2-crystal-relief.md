# Ultima Weapon V2 — 三層水晶 3D 浮雕修正 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `/cloud-ultima-weapon-v2` 的三層內部水晶從「埋在白色外殼裡」改成真正的前後對稱 3D 浮雕階梯，同時讓白色外殼收縮成頸部接到三角金屬夾、並與四根紅色驅動器留出可量測的空隙。

**Architecture:** 全部幾何來自單一 hand-authored factory `createUltimaWeaponV2Model.ts`。修正只改常數、station 陣列與兩個 section helper，不新增/刪除任何 mesh（18 個物理零件的 contract 由 `spec/check_centerline.py` 雙向斷言）。新的關係一律**由建構導出**（像既有的 `driverRootRadius()`），能導出的就不要另外斷言；導不出的才加閘門。

**Tech Stack:** TypeScript + three.js（純程式幾何，無外部 mesh／貼圖）、Vue 3 + vite-ssg、Python 3 gate scripts、`tools/capture_ultima.mjs`（headless 截圖）。

## Global Constraints

- 座標系：`+Y` guard→tip、`−Y` guard→pommel、`+Z` 面向藍本、原點在 blade socket；`U = 0.01`，所有常數以 normalized-1000 書寫。
- **零件 contract 不可增減**：18 個 mesh + 3 個 organisational group。`centralGripSocket` 與任何 `driverSocket*` 一律不得存在。
- 所有中心零件必須落在 `X = 0`（|minX+maxX| ≤ 0.001 world），5 組鏡射對必須互為反射。
- 所有刀身水晶必須以 `Z = 0` 為對稱面，前後等深；不得只往前推。
- **文件中每個數字只能追溯到產物**（`artifacts/ultima-v2/full/parts.json`、`artifacts/ultima-v2/gate/*.json`）或 factory 原始碼，不得抄另一份文件。`spec/audit_records.py` 會擋。
- 管線順序不可換：`author_spec.py` → capture renders → `run_gates.sh` → `record_reviews.sh`（×3）。`author_spec.py` 每次執行都會清空 `reviewHistory`。
- 回覆語言：繁體中文（台灣用語）。

---

## 已完成的藍本放大核對（不必重做，除非數字有疑）

依 `CLAUDE.md`「接合處放大核對是主要驗收法則」，本計畫的所有讀數來自：

| Crop（按接合處切）       | 區域（artwork px）       | 倍率 | 讀到什麼                                                          |
| ------------------------ | ------------------------ | ---- | ----------------------------------------------------------------- |
| `j1-shell-base-to-clamp` | (95,265)–(165,335)       | 12×  | 白色外殼下緣**確實終止於黑色三角夾**，不再往下延伸                |
| `j2-diamond-and-clamps`  | (100,275)–(155,330)      | 14×  | 紅色菱形是**細長楔形**、亮紅邊 + 暗紫核；深色核心只是它的一圈薄邊 |
| `j3/j4-shell-vs-drivers` | (55,285)/(120,270) +80px | 10×  | 外殼輪廓與紅色桿之間**看得到白色背景**，兩者不相接                |

`spec/measurements.json` 的 `shellWidthProfile` 是同一份藍本的機器讀數：

```
y=25  minX −86.5  maxX +81.7   width 168.2
y=50  minX −110.3 maxX +81.5   width 191.8   ← 左側 −110 是投影/遮擋假影（右側才是乾淨邊）
y=75  minX −113.3 maxX +80.7   width 194.0
y=100 minX −83.8  maxX +79.8   width 163.6
y=0   minX +32.9  maxX +70.6   width 37.7    ← 整段被刀柄遮住，只剩右側一條
```

### 與規格衝突之處（照規格做，但在此明講）

1. **藍本沒有收縮頸。** 右側乾淨邊在 y=25…100 幾乎是常數 ~80–82 半寬，y=20 以下被刀柄完全遮住。使用者規格 §10 要求外殼從淺紫水晶底部收縮到 clamp 接點，**照做**；收縮完全落在 y<42 的遮擋區，只有 Y=42 的半寬 72 比藍本讀到的 ~82 窄 12%（§14 允許 6–14%）。
2. **驅動器總跨距不合 §14 的 34–39%。** 實測是 319.46 / 971 = **32.9%**。要補足得把 `DRIVER_RADIAL_END` 從 172 拉到 178.5，那是量出來的值，且此項不在 §23 的驗收清單裡。**不改**，維持量測值。
3. §17 建議 `opacity 0.52–0.64`，但本 repo 的 render review 曾把它從 0.62 提到 0.70（0.62 時外殼在白底上糊掉）。取 **0.64**（規格上限）作為折衷——幾何已負責露出內層，透明度不再是主要手段。

---

## File Structure

| 檔案                                                               | 責任                                   | 本次動作                                                                     |
| ------------------------------------------------------------------ | -------------------------------------- | ---------------------------------------------------------------------------- |
| `src/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model.ts` | 唯一幾何來源                           | 改常數、SHELL_STATIONS、CORE 幾何、bluntSection、guardCore outline、外殼材質 |
| `src/exhibits/cloud-ultima-weapon-v2/spec/check_centerline.py`     | 從 `parts.json` 斷言 contract / 中心線 | **新增**浮雕深度階梯 + Z 對稱斷言                                            |
| `src/exhibits/cloud-ultima-weapon-v2/spec/audit_records.py`        | 文件數字 vs 產物                       | **新增** shell↔driver 前視圖淨空計算與 gate                                  |
| `src/exhibits/cloud-ultima-weapon-v2/spec/author_spec.py`          | 產生 `object-sculpt-spec.json`         | 加入浮雕 local features、淨空／接點 anchors、前後對稱                        |
| `src/exhibits/cloud-ultima-weapon-v2/spec/CURRENT-MODEL.md`        | 模型現況                               | 依新 `parts.json` 重新取數                                                   |
| `src/exhibits/cloud-ultima-weapon-v2/spec/RELATIONSHIPS.md`        | 檔案相依關係                           | 補新的 load-bearing 關係                                                     |
| `src/exhibits/cloud-ultima-weapon-v2/spec/confidence-report.md`    | 每個數字為何是這個值                   | 依新 gate JSON 重新取數                                                      |

---

### Task 1: 深度基準與三層浮雕階梯

**Files:**

- Modify: `src/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model.ts`

**Interfaces:**

- Produces: `SHELL_HALF_DEPTH_REF = 14`、`T = 28`、`INSERT_HALF_DEPTH`、`CORE_HALF_DEPTH`、`GEM_HALF_DEPTH`（Task 2、5、6 都引用）

- [ ] **Step 1: 加入深度基準常數**（放在 `SHELL_STATIONS` 上方）

```ts
/**
 * Depth reference. `T` is the shell's total front-to-back thickness in the lower-middle blade,
 * and every inner crystal's depth is written as T plus its own protrusion — so the relief order
 * cannot be reversed by editing one number. Correction spec §4/§8.
 */
const SHELL_HALF_DEPTH_REF = 14;
const T = SHELL_HALF_DEPTH_REF * 2;

/** Each layer = the layer under it + its own per-side protrusion. §5, §6, §7. */
const INSERT_HALF_DEPTH = SHELL_HALF_DEPTH_REF + 0.1 * T; // 16.8 → 1.20 T total
const CORE_HALF_DEPTH = INSERT_HALF_DEPTH + 0.065 * T; //    18.62 → 1.33 T total
const GEM_HALF_DEPTH = CORE_HALF_DEPTH + 0.12 * T; //        21.98 → 1.57 T total
```

- [ ] **Step 2: 換掉舊的三個深度常數**

刪除 `const CORE_HALF_DEPTH = 4;` 與 `const GEM_HALF_DEPTH = 17;`（含 `GEM_HALF_DEPTH` 上方那句「deeper than the shell here (11–14)」註解，已被 Step 1 的說明取代）。

- [ ] **Step 3: `INSERT_STATIONS` 改用新深度**

```ts
const INSERT_STATIONS: [number, number, number][] = [
  [42, 43, INSERT_HALF_DEPTH],
  [380, 28, INSERT_HALF_DEPTH * 0.88],
  [480, 0, 0],
];
```

`0.88` 的理由寫進註解：Y=380 處外殼半深是 12.2，插件 14.78 仍外凸 2.58＝0.092 T，滿足 §5 的最小 0.08 T。

- [ ] **Step 4: `bluntSection` 的斜面收窄到全寬 6%**

把兩處 `halfWidth * 0.62` 改成 `halfWidth * 0.88`，並更新 docstring（現有 docstring 提到不存在的 `frontProud` 參數、又說「flat back」但程式其實前後都做倒角，兩句都是舊的）。

```ts
/**
 * The inner crystals' cross-section: a flat raised plateau with a narrow faceted bevel down to
 * the side edges, symmetric in Z. It may taper in silhouette but it must never receive the
 * shell's knife-edge profile — these are raised crystal reliefs, not a second cutting edge.
 *
 * The bevel spans 12% of the half-width, i.e. 6% of the full width, which is the top of the
 * correction spec's 3–6% band (§5): wide enough that the facet catches a different light step
 * than the plateau, narrow enough that the layer still reads as a raised slab, not a lens.
 */
function bluntSection(y: number, halfWidth: number, halfDepth: number): THREE.Vector3[] {
  const chamfer = halfDepth * 0.55;
  const pts: [number, number][] = [
    [-halfWidth, -chamfer],
    [-halfWidth * 0.88, -halfDepth],
    [halfWidth * 0.88, -halfDepth],
    [halfWidth, -chamfer],
    [halfWidth, chamfer],
    [halfWidth * 0.88, halfDepth],
    [-halfWidth * 0.88, halfDepth],
    [-halfWidth, chamfer],
  ];
  return pts.map(([x, z]) => new THREE.Vector3(n(x), n(y), n(z)));
}
```

- [ ] **Step 5: `darkCoreTriangle` 改成 loft + bluntSection**

新增 station 陣列（放在 `CORE_*` 常數之後）：

```ts
/**
 * The dark core is a raised faceted prism, not an extruded flat triangle: at 1.33 T deep a
 * square-rimmed extrusion reads as an opaque plate stuck on the front, which §6 rejects. Depth
 * stays at full CORE_HALF_DEPTH until the outline has almost closed, so the core never falls
 * behind the purple insert it is supposed to sit proud of.
 */
const CORE_STATIONS: [number, number, number][] = [
  [CORE_BASE_Y, CORE_HALF_WIDTH, CORE_HALF_DEPTH],
  [100, CORE_HALF_WIDTH * 0.184, CORE_HALF_DEPTH * 0.62],
  [CORE_APEX_Y, 0, 0],
];
```

再把建構處從 `extrudeOutline([...], CORE_HALF_DEPTH)` 換成：

```ts
const coreGeometry = loft(CORE_STATIONS.map(([y, hw, hd]) => bluntSection(y, hw, hd)));
```

- [ ] **Step 6: `GEM_HALF_DEPTH` 生效檢查**

`rootDiamondGem` 的 loft 已經用 `GEM_HALF_DEPTH` 建前後兩個尖點，不需改建構碼；只要 Step 1/2 換掉常數即可。更新它上方的註解，說明它現在是最突出的一層（1.57 T）。

- [ ] **Step 7: typecheck**

Run: `npx vue-tsc --noEmit`
Expected: 0 errors。

- [ ] **Step 8: Commit**

```bash
git add src/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model.ts
git commit -m "feat(ultima-v2): 三層水晶改為前後對稱浮雕階梯（1.20/1.33/1.57 T）"
```

---

### Task 2: 外殼收縮頸、clamp 接點與 guardCore 補洞

**Files:**

- Modify: `src/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model.ts`

**Interfaces:**

- Consumes: Task 1 的 `SHELL_HALF_DEPTH_REF`
- Produces: `clampOuterEdgeX(y)`、`SHELL_BASE_Y = 20`（Task 4 的淨空計算引用 `SHELL_STATIONS`）

- [ ] **Step 1: 加入 clamp 外緣求值函式**（放在 `CLAMP_OUTLINE` 與 `CLAMP_HALF_DEPTH` 之後）

```ts
/**
 * The clamp's outer edge (inner-upper vertex → outer vertex) evaluated at height y.
 *
 * Derived, not typed in: the shell's base half-width IS this value at the shell's base height,
 * so the shell-to-clamp contact the correction spec §10 asks for holds by construction. Narrow
 * the clamp outline and the shell's neck follows it automatically.
 */
const clampOuterEdgeX = (y: number): number => {
  const [[ix, iy], , [ox, oy]] = CLAMP_OUTLINE;
  return ix + ((ox - ix) * (iy - y)) / (iy - oy);
};

/**
 * Where the shell hands the blade to the clamps. At Y=20 the clamp spans x 2.83…29.14 and the
 * gem spans 0…2.83, so the shell's base ring is completely backed by metal and gem — no pale
 * wedge shows between the jaws, and nothing pale exists below them at all.
 */
const SHELL_BASE_Y = 20;
```

- [ ] **Step 2: 換掉 `SHELL_STATIONS`**

```ts
const SHELL_STATIONS: [number, number, number][] = [
  // Below Y_TRANSITION (the purple insert's base, Y=42) the shell is a converging NECK that
  // ends exactly on the two clamps' outer edges. Above it the measured artwork silhouette is
  // unchanged. The crop reads a near-constant ~82 half-width right down to y=25 and is fully
  // occluded by the hilt below that (its own profile collapses to a 37.7-wide sliver at y=0),
  // so the neck lives where the crop constrains nothing — but the 72 at Y=42 IS 12% under the
  // crop's ~82, spent to buy the full 1.00-diameter driver clearance §13 prefers.
  [SHELL_BASE_Y, clampOuterEdgeX(SHELL_BASE_Y), 11], // 29.14 — the two clamp contact points
  [42, 72, 13], // Y_transition: 144 wide = 45.1% of the 319.46 driver span (§14 wants 44–50%)
  [70, 82, SHELL_HALF_DEPTH_REF], // the widest point, moved up 25 from Y=45 (§14 allows ≤29)
  [110, 81, SHELL_HALF_DEPTH_REF],
  [300, 73, 13],
  [500, 63, 11],
  [575, 54, 10], // the taper's knee
  [650, 34, 8],
  [760, 0, 0], // tip
];
```

刪掉舊的 `[8, 66, 11] / [25, 85, 13] / [45, 88, 14]` 三站與它們上方那段已失效的長註解（講 Y=8 vs Y=4 的那段——shell base 現在是 20，離 clamp base 6 遠得多）。

- [ ] **Step 3: `guardCore` 頂邊改用 clamp 下緣**

```ts
const guardCore = mesh(
  extrudeOutline(
    [
      [-BRIDGE_HALF_WIDTH, BRIDGE_BOTTOM_Y],
      [BRIDGE_HALF_WIDTH, BRIDGE_BOTTOM_Y],
      // The top edge IS the two clamps' own lower edges, so the wedge between the jaws and the
      // hilt closes by construction. Without it that wedge was a void the old wide shell base
      // happened to cover; with the shell contracted it would have opened as a black gap (§12).
      [CLAMP_OUTLINE[2]![0], CLAMP_OUTLINE[2]![1]],
      [CLAMP_OUTLINE[1]![0], CLAMP_OUTLINE[1]![1]],
      [-CLAMP_OUTLINE[2]![0], CLAMP_OUTLINE[2]![1]],
    ],
    BRIDGE_HALF_DEPTH,
  ),
  materials.guardSteel,
  { id: "guardCore", explodeDirection: [0, -0.25, 0] },
  hiltGroup,
);
```

刪除 `BRIDGE_TOP_Y`（改用 clamp 幾何後不再有引用）。

- [ ] **Step 4: typecheck**

Run: `npx vue-tsc --noEmit`
Expected: 0 errors（特別確認 `BRIDGE_TOP_Y` 沒有殘留引用）。

- [ ] **Step 5: Commit**

```bash
git add src/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model.ts
git commit -m "feat(ultima-v2): 外殼收縮成頸部接上三角夾，guardCore 封住夾具下方空洞"
```

---

### Task 3: 外殼材質回到規格區間

**Files:**

- Modify: `src/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model.ts`（`buildMaterials()` 的 `outerCrystal`）

- [ ] **Step 1: 改兩個值並改寫理由註解**

```ts
// Milky translucent crystal, not opaque grey plastic. `opacity` had been lifted to 0.70 in an
// earlier render review because the shell washed out at 0.62; it comes back to 0.64 — the top
// of the correction spec's 0.52–0.64 band — now that the three inner crystals protrude through
// the shell's faces and no longer depend on seeing through it. `depthWrite: false` is what
// keeps the inner crystals from being depth-culled by the shell.
const outerCrystal = new THREE.MeshPhysicalMaterial({
  // …
  opacity: 0.64,
  transmission: 0.25,
  // …
});
```

- [ ] **Step 2: Commit（與 Task 4 合併提交亦可）**

---

### Task 4: 機械閘門 — 浮雕深度階梯與驅動器淨空

自評不算驗收；這兩項是 §23 唯一還沒有機械閘門的驗收條件。

**Files:**

- Modify: `src/exhibits/cloud-ultima-weapon-v2/spec/check_centerline.py`
- Modify: `src/exhibits/cloud-ultima-weapon-v2/spec/audit_records.py`

**Interfaces:**

- Consumes: `artifacts/ultima-v2/full/parts.json` 的每個 part `bounds`（含 `minZ`/`maxZ`）；factory 原始碼的 `SHELL_STATIONS`、`DRIVER_*`、`CONNECTOR_*`

- [ ] **Step 1: `check_centerline.py` 加浮雕深度階梯斷言**

在 `MIRRORED` 之後加常數：

```python
# Correction spec section 4/8: the four blade layers form a relief ladder, each deeper than the
# one it sits on, every one symmetric about Z=0. T is the shell's own total depth, so these
# ratios are read out of the build rather than trusted from the source.
RELIEF = [
    ("purpleEnergyInsert", 1.16, 1.22),
    ("darkCoreTriangle", 1.28, 1.36),
    ("rootDiamondGem", 1.55, 1.70),
]
```

在 shell/clamp 檢查之後、`ON_AXIS` 迴圈之前加：

```python
    def depth(name: str) -> float | None:
        b = bounds.get(name)
        return None if not b else b["maxZ"] - b["minZ"]

    T = depth("outerCrystalShell")
    if T:
        for name, lo, hi in RELIEF:
            d = depth(name)
            if d is None:
                failures.append(f"{name}: not present in the built model")
                continue
            ratio = d / T
            status = "ok " if lo <= ratio <= hi else "OFF"
            print(f"{status} {name:<24} depth {ratio:.3f} T  (want {lo}–{hi})")
            if not lo <= ratio <= hi:
                failures.append(f"{name}: depth is {ratio:.3f} T, outside {lo}–{hi} T")
        for name in ("outerCrystalShell", *[r[0] for r in RELIEF]):
            b = bounds.get(name)
            if b and abs(b["minZ"] + b["maxZ"]) > TOLERANCE:
                failures.append(
                    f"{name}: relief is not symmetric about Z=0 "
                    f"(centre {(b['minZ'] + b['maxZ']) / 2:+.5f}) — front-only extrusion"
                )
```

- [ ] **Step 2: 跑一次，確認在改模型前它會 FAIL**

Run: `python3 src/exhibits/cloud-ultima-weapon-v2/spec/check_centerline.py`
Expected: 用**舊的** `parts.json` 時 FAIL（舊 insert 深度只有 0.43 T）。若 Task 1 已先合併，就會 PASS——兩種結果都可接受，只要確認斷言真的有讀到值、不是靜默跳過。

- [ ] **Step 3: `audit_records.py` 加驅動器淨空計算**

在既有的 driver-root 推導之後加入（沿用同一批 `const()` 讀出的常數）：

```python
# --- front-view shell-to-driver clearance, recomputed from the factory's own stations --------
# Correction spec section 13: the pale shell may not touch or nearly touch a red driver. This is
# the one acceptance criterion with no other mechanical home -- part bounds are axis-aligned
# boxes and would report an overlap where there is clear space.
stations = [
    tuple(float(v) for v in row)
    for row in re.findall(
        r"\[\s*([-\d.]+)\s*,\s*([-\d.\w()* ]+?)\s*,\s*([-\d.\w* ]+?)\s*\]",
        re.search(r"const SHELL_STATIONS[^=]*= \[(.*?)\n\];", SRC, re.S).group(1),
    )
    if row[0].replace(".", "").replace("-", "").isdigit()
    and row[1].replace(".", "").replace("-", "").isdigit()
]
```

> **實作註記：** `SHELL_STATIONS` 的第一站半寬是 `clampOuterEdgeX(SHELL_BASE_Y)` 這個運算式，正則抓不到。實作時改成**在 factory 匯出一份純數值的 `SHELL_PROFILE`**，或在 audit 裡把 clamp 外緣公式也重算一次。採後者（與 `driverRootRadius` 同一種做法，不動 runtime 產物）：

```python
clamp_pts = [
    (float(a), float(b))
    for a, b in re.findall(r"\[(-?[\d.]+), (-?[\d.]+)\]",
                           re.search(r"const CLAMP_OUTLINE[^=]*= \[(.*?)\n\];", SRC, re.S).group(1))
]
(ix, iy), _, (ox, oy) = clamp_pts
shell_base_y = const(r"^const SHELL_BASE_Y = (-?[\d.]+)")
rows = re.findall(r"^\s*\[(-?[\d.]+), (-?[\d.]+), ",
                  re.search(r"const SHELL_STATIONS[^=]*= \[(.*?)\n\];", SRC, re.S).group(1), re.M)
profile = [(shell_base_y, ix + (ox - ix) * (iy - shell_base_y) / (iy - oy))]
profile += [(float(y), float(w)) for y, w in rows]
profile.sort()


def shell_half_width(y: float) -> float:
    if y < profile[0][0] or y > profile[-1][0]:
        return 0.0
    for (y0, w0), (y1, w1) in zip(profile, profile[1:]):
        if y0 <= y <= y1:
            return w0 + (w1 - w0) * (y - y0) / (y1 - y0) if y1 > y0 else w0
    return 0.0


clearance = {}
for band, elev in (("upper", const(r"DRIVER_ELEVATION_DEG = \{ upper: (-?[\d.]+)")),
                   ("lower", const(r"DRIVER_ELEVATION_DEG = \{.*lower: (-?[\d.]+)"))):
    e = math.radians(elev)
    r0 = math.hypot(*[roots[band][0], roots[band][1] - centre_y])
    r1 = const(r"^const DRIVER_RADIAL_END = (-?[\d.]+)")
    worst = min(
        (r0 + (r1 - r0) * i / 200) * math.cos(e) - rod_r * math.sin(e)
        - shell_half_width(centre_y + (r0 + (r1 - r0) * i / 200) * math.sin(e) + rod_r * math.cos(e))
        for i in range(201)
    )
    clearance[band] = worst
    print(f"DERIVED {band} driver front-view clearance {worst:.1f} "
          f"= {worst / (2 * rod_r):.2f} x driver diameter")
    if worst < 0.75 * 2 * rod_r:
        fail.append(f"{band} driver clears the shell by only {worst / (2 * rod_r):.2f} "
                    f"driver diameters — correction spec section 13 requires 0.75")
```

- [ ] **Step 4: 跑 audit，確認算出的數值與手算相符**

Run: `python3 src/exhibits/cloud-ultima-weapon-v2/spec/audit_records.py`
Expected: 印出 `upper driver front-view clearance ≈ 22.3 = 1.01 x driver diameter`、`lower ≈ 118 = 5.4 x`；不因淨空 fail。

- [ ] **Step 5: Commit**

```bash
git add src/exhibits/cloud-ultima-weapon-v2/spec/check_centerline.py \
        src/exhibits/cloud-ultima-weapon-v2/spec/audit_records.py \
        src/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model.ts
git commit -m "test(ultima-v2): 浮雕深度階梯與驅動器淨空改由閘門斷言"
```

---

### Task 5: spec 的零件與接合處關係

**Files:**

- Modify: `src/exhibits/cloud-ultima-weapon-v2/spec/author_spec.py`
- Regenerate: `src/exhibits/cloud-ultima-weapon-v2/spec/object-sculpt-spec.json`

- [ ] **Step 1: 讀 `author_spec.py` 現有的 component 結構**

Run: `python3 -c` 不可用（被政策擋）。改用 `ctx_read` 讀 `spec/author_spec.py`，找出各 component 的 `localFeatures` / `qualityContract` / anchors 欄位名稱。

- [ ] **Step 2: 為四個刀身零件補 local features**

每個都要寫成**可量測**的句子（不是形容詞）：

- `outerCrystalShell`：「total depth 1.00 T at the lower-middle blade; converges below Y=42 to the two clamp outer-edge contact points at (±29.14, 20); no geometry below Y=20」
- `purpleEnergyInsert`：「1.16–1.22 T total depth, protruding 0.10 T per side beyond both shell faces; bevel 6% of local full width; symmetric about Z=0」
- `darkCoreTriangle`：「1.28–1.36 T; protrudes 0.05–0.08 T per side beyond the insert; faceted prism, unsharpened」
- `rootDiamondGem`：「1.55–1.70 T; protrudes 0.10–0.17 T per side beyond the dark core; complete outline visible front and rear; lower edges contact both clamps' inner upper edges」

- [ ] **Step 3: quality contract 加兩條**

- 「front-view shell-to-driver gap ≥ 0.75 × driver diameter (preferred 1.00); 3D surface clearance ≥ 0.25 ×」
- 「front and rear relief identical: every blade layer's Z bounds centre on 0 within 0.001 world」

- [ ] **Step 4: anchors 加 shell↔clamp 接點**

`outerCrystalShell.lowerLeftContact` / `lowerRightContact` = (∓29.14, 20)；對應 `crystalClamp{Left,Right}.outerEdge`。

- [ ] **Step 5: 重新產生 spec**

Run: `python3 src/exhibits/cloud-ultima-weapon-v2/spec/author_spec.py`
Expected: 寫出 `object-sculpt-spec.json`，`reviewHistory` 被清空（預期行為）。

- [ ] **Step 6: Commit**

```bash
git add src/exhibits/cloud-ultima-weapon-v2/spec/author_spec.py \
        src/exhibits/cloud-ultima-weapon-v2/spec/object-sculpt-spec.json
git commit -m "spec(ultima-v2): 補上浮雕深度、外殼淨空與 shell↔clamp 接點關係"
```

---

### Task 6: 重跑整條管線並驗收

**Files:**

- Produces: `artifacts/ultima-v2/**`、`spec/silhouette-report.json`

- [ ] **Step 1: 確認 dev server 在跑（capture 需要它）**

Run: `lsof -nP -iTCP:3001 -sTCP:LISTEN`
若沒有：`npm run dev`（背景執行）。`capture_ultima.mjs` 走 `--route ultima-v2-harness`。

- [ ] **Step 2: 依序重跑（順序不可換）**

```bash
cd /Users/tonyyang/git/personal/img2three-art-exhibition
python3 src/exhibits/cloud-ultima-weapon-v2/spec/author_spec.py
for v in front-orthographic back-orthographic left-side-thickness right-side-thickness \
         assembled-three-quarter rear-three-quarter artwork-match exploded-three-quarter \
         closeup-crystal-clamp closeup-clamp-bases closeup-driver-joints \
         closeup-connectors closeup-spinner-ends closeup-grip-pommel; do
  node tools/capture_ultima.mjs --route ultima-v2-harness --out artifacts/ultima-v2/full --detail full --views $v
done
node tools/capture_ultima.mjs --route ultima-v2-harness --out artifacts/ultima-v2/flat       --detail full       --views artwork-match --flat
node tools/capture_ultima.mjs --route ultima-v2-harness --out artifacts/ultima-v2/blockout   --detail blockout   --views artwork-match
node tools/capture_ultima.mjs --route ultima-v2-harness --out artifacts/ultima-v2/structural --detail structural --views artwork-match
zsh src/exhibits/cloud-ultima-weapon-v2/spec/run_gates.sh
```

Expected：`component contract + centreline` 段落全 `ok`，含新的三行 depth 斷言；`records match the artifacts` 印出兩個 driver clearance 並 PASS。

- [ ] **Step 3: 放大比對——這是驗收，不是自評**

寫一支 scratchpad 腳本，把 `artifacts/ultima-v2/full/front-orthographic.png` 與藍本同一接合處**並排**放大（≥6×、NEAREST），逐點看：

1. 淺紫浮出白殼、深紫再浮出一層、紅菱形最突出（側視圖判讀）
2. 白殼下緣終止於兩個 clamp 接點，夾具下方無白色
3. 四根紅桿與白殼之間看得到背景
4. 刀身→刀柄沒有白色縫隙、夾具下方沒有黑洞

任何一項不過就回 Task 1/2 調數字，**不要**改成調透明度。

- [ ] **Step 4: 三輪 review 寫回**

Run: `zsh src/exhibits/cloud-ultima-weapon-v2/spec/record_reviews.sh`（跑 3 次；pass 是逐輪解鎖的）

- [ ] **Step 5: 端到端**

```bash
npx vue-tsc --noEmit && npx vite-ssg build
node tools/verify_v2_route.mjs
```

Expected: build 成功；route 驗證 12 個面板控制項都不丟 console error。

---

### Task 7: 文件數字重新取自產物

**Files:**

- Modify: `spec/CURRENT-MODEL.md`、`spec/RELATIONSHIPS.md`、`spec/confidence-report.md`

- [ ] **Step 1: 從產物取數，不要抄舊文件**

`artifacts/ultima-v2/full/parts.json` → 節點數、三角面數、world bounds；
`artifacts/ultima-v2/gate/tier1-*.json` → ΔE、aspect/scale；
`spec/silhouette-report.json` → IoU。

- [ ] **Step 2: `audit_records.py` 的 `FAMILIES` 退休值清單要補**

三角面數、IoU 會變。把舊值加進對應 family 的 retired 清單，live 值由腳本自己從產物讀。

- [ ] **Step 3: `RELATIONSHIPS.md` §5 補三條 load-bearing 關係**

| 斷言                                              | 位置                    | 抓到什麼                               |
| ------------------------------------------------- | ----------------------- | -------------------------------------- |
| 浮雕深度階梯 1.20/1.33/1.57 T                     | `check_centerline.py`   | 有人只調不透明度、或把某層改回埋在殼裡 |
| 四層 Z 對稱                                       | 同上                    | 只往前推的單面浮雕                     |
| shell↔driver 前視圖淨空                           | `audit_records.py`      | 外殼變寬或驅動器內移                   |
| shell base 半寬 = `clampOuterEdgeX(SHELL_BASE_Y)` | factory（導出，非斷言） | 改 clamp 輪廓時外殼自動跟上            |

- [ ] **Step 4: gate 綠燈**

Run: `python3 src/exhibits/cloud-ultima-weapon-v2/spec/audit_records.py`
Expected: `PASS  N documents, every figure traced to an artifact`

- [ ] **Step 5: Commit**

```bash
git add -A src/exhibits/cloud-ultima-weapon-v2 artifacts/ultima-v2
git commit -m "docs(ultima-v2): 依新產物重新取數，補浮雕與淨空的關係鏈"
```

---

### Task 8: SUCCINCT 精簡 spec

**Files:**

- Modify: `spec/CURRENT-MODEL.md`、`spec/RELATIONSHIPS.md`、`spec/confidence-report.md`、`spec/image-analysis.md`、`spec/reference-suitability.md`、`spec/node-inventory.md`

- [ ] **Step 1: 派 `/ponytail:ponytail-review` 為 opus max subagent**

用 Agent tool，`model: "opus"`，任務是「只獵複雜度」：找出 spec 文件中重複、可從產物推導、或已被程式斷言而不需再用散文重述的段落，逐條給「位置／砍什麼／誰取代它」。

- [ ] **Step 2: 自己同步做一輪 SUCCINCT 判準**

一段留下的條件（任一）：

1. 它是**唯一**記錄某個決策「為什麼」的地方；
2. 它記錄某個**衝突**（藍本讀成 X、規格要 Y、做了 Y）；
3. 它是**接手必讀**的順序或陷阱。

砍掉的：程式或 gate 已經斷言的重述、同一數字的第二份拷貝、可從 `parts.json` 直接讀出的表格、鋪陳語。

- [ ] **Step 3: 合併兩份結果，只採兩邊都同意或有明確理由的刪除**

- [ ] **Step 4: `audit_records.py` 必須仍然綠燈**（砍文件不能砍掉 live 值旁註）

Run: `python3 src/exhibits/cloud-ultima-weapon-v2/spec/audit_records.py`

- [ ] **Step 5: Commit**

```bash
git add src/exhibits/cloud-ultima-weapon-v2/spec
git commit -m "docs(ultima-v2): spec 以 SUCCINCT 為最高原則精簡"
```

---

## Self-Review

**Spec coverage（使用者 prompt 的 24 節）**

| 節                                  | 由哪個 Task 涵蓋                                                    |
| ----------------------------------- | ------------------------------------------------------------------- |
| §1 設計意圖、§2 零件 contract       | 既有 contract 不動，Task 4 的斷言保護                               |
| §3 座標系、§4 深度基準              | Task 1 Step 1                                                       |
| §5 淺紫浮雕、§6 深紫浮雕、§7 紅菱形 | Task 1 Step 3/4/5/6                                                 |
| §8 漸進浮雕順序                     | Task 1 Step 1（由建構導出）+ Task 4 斷言                            |
| §9 水平轉換線／中心線               | 既有 `ON_AXIS` 斷言已涵蓋，無需改動                                 |
| §10 下段外殼收縮                    | Task 2 Step 1/2                                                     |
| §11 菱形與夾具關係                  | 既有 `CLAMP_OUTLINE` 由 gem 導出，不動                              |
| §12 刀身→刀柄接合                   | Task 2 Step 3（guardCore 封洞）                                     |
| §13 外殼與驅動器淨空                | Task 2（收窄外殼）+ Task 4（閘門）                                  |
| §14 比例修正上限                    | Task 2 Step 2 註解逐條記錄；跨距 32.9% 的偏離已在上方「衝突」節說明 |
| §15 側視品質、§16 前後對稱          | Task 1（bluntSection 前後對稱）+ Task 4（Z 對稱斷言）               |
| §17 外殼材質、§18 內層材質          | Task 3（§18 現況已符合，不動）                                      |
| §19 刀柄既有規則                    | 不動；`check_centerline.py` 已雙向斷言                              |
| §20 執行順序、§21 分工              | Task 5/6（幾何先於材質；本次以 inline 執行，不派 6 個 subagent）    |
| §22 驗證 render                     | Task 6 Step 2 的 14 個 view + Step 3 的並排放大                     |
| §23 可量測驗收                      | Task 4 的兩支閘門 + 既有 `front_rear_overlay.py`                    |
| §24 硬性拒絕條件                    | 全部對應到 Task 4 的斷言或 Task 6 Step 3 的放大比對                 |

**Placeholder scan：** 無 TBD／「稍後補」。唯一的實作分歧點（Task 4 Step 3 正則抓不到運算式）已寫出採用哪一種做法與原因。

**Type consistency：** `SHELL_HALF_DEPTH_REF` / `T` / `INSERT_HALF_DEPTH` / `CORE_HALF_DEPTH` / `GEM_HALF_DEPTH` / `clampOuterEdgeX` / `SHELL_BASE_Y` / `CORE_STATIONS` 在 Task 1、2、4、5 之間名稱一致。`BRIDGE_TOP_Y` 在 Task 2 Step 3 刪除，Step 4 的 typecheck 負責攔殘留引用。

**已知偏離（不修，已說明理由）：**

1. 驅動器總跨距 32.9%，§14 要 34–39% —— 那是量測值，且不在 §23 驗收清單。
2. 外殼 opacity 取 0.64 而非更低 —— §17 區間上限，本 repo 曾實測 0.62 會糊掉。
3. §5 的「shell 凹槽」未做 —— 規格寫的是 "may"；插件靠外凸即滿足「partially seated + 可見浮起」，凹槽只會多一組共面風險。

---

## 執行結果（2026-08-07，commit `385f4ea`）

Task 1–7 全數完成，inline 執行。與計畫的兩處差異：

1. **`SHELL_BASE_Y` 訂為 13，不是 20。** 計畫的 20 讓 blockout tier-1 IoU 掉到 0.8448，低於
   0.85 門檻。降到 13——gem 底點、也是兩個夾具交會的高度——把面積補回來，IoU 回到 **0.8505**，
   而且錨點更有意義：外殼止於兩顎相接處。淨空不受影響（最窄處在 Y=42，仍是 22.4）。
2. **`audit_records.py` 的淨空計算採「在 audit 裡重算 clamp 外緣」那一版**，如計畫 Task 4
   Step 3 的實作註記所述。正則抓得到 `SHELL_STATIONS` 第 2 站起的純數值列，第一站的
   `clampOuterEdgeX(SHELL_BASE_Y)` 由 `CLAMP_OUTLINE` + `SHELL_BASE_Y` 重算。

**閘門負向對照**（證明閘門不是永遠亮綠燈）：同一條公式餵舊的 `SHELL_STATIONS`，上排驅動器
淨空算出 **−0.40 個桿徑**——正是修正前 render 裡紅桿沒入外殼的那個缺陷。新值 +1.02。

**最終產物數字**：748 tris、21 節點 / 18 mesh、IoU 0.8875、blockout 0.8505、前後對稱 0.9987、
浮雕階梯 1.200 / 1.330 / 1.570 T、上排驅動器淨空 1.02 個桿徑。ΔE 61.94 仍未過（既有的
documented limitation，非本次引入）。
