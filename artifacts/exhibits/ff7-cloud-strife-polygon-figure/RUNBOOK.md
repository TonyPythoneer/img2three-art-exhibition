# RUNBOOK — Cloud Strife Polygon Figure

執行 task 只需要看這一個檔案。每一段的指令都可以直接貼進 Claude Code。

- 規格權威：`prompt.txt`（量測值、palette、十個 part 的定義）
- 機器規格：`spec/object-sculpt-spec.json`（33 components / 11 materials，validate + strict 皆綠）
- 進度：Claude Code 的 task list（#4–#15）
- 路徑約定：以下都以 repo 根目錄為 cwd

```bash
EXHIBIT=artifacts/exhibits/ff7-cloud-strife-polygon-figure
SKILL=~/.claude/skills/img2threejs           # forge 腳本必須從這裡執行
```

---

## 0. 每次開工前，先過狀態閘門

```bash
cd $SKILL && python3 forge/next.py \
  --state ~/git/personal/img2three-art-exhibition/artifacts/exhibits/ff7-cloud-strife-polygon-figure/.img2threejs/state.json \
  ~/git/personal/img2three-art-exhibition/artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/object-sculpt-spec.json
```

exit code `3` 或 `status=stopped` 是硬停：回報原因，不要繞過、不要從記憶重建進度。

目前它停在 `step=build-current-pass, pass=blockout`。

---

## ⛔ 閘門（task #16）

**在使用者對 spec 放行之前，下面 #4 起的任何一條都不准跑。** 待決的三件事：

1. 材質 roughness：spec 契約寫 0.80–0.90，材質實際 0.68–0.70（工具反推值）。二選一。
2. 貼圖解析度 1024 → 256（agent 已改，需追認）。
3. `analyze_texture.py` 判 6 個材質為 `painted-metal` 要塞 `clearcoat: 1.0`，已被推翻保留霧面。

---

## Stage 1 — 十個 part，各自獨立，不整合（task #4–#12）

十條彼此不相依，可以同時開十個 agent 跑。每一條的交付物固定是：

- `$EXHIBIT/parts/create<Part>.ts`，export `create<Part>(options): THREE.Group`
- 原點放在該 part 的 socket 點（見 `prompt.txt` §3），Stage 2 才能純擺放
- `group.userData.sockets = { name: Vector3 }`
- 三張 render（正面＋對應側面＋一個 3/4）對照 reference，**≥6× NEAREST**
- 猜測清單：部位／兩種讀法／選了哪個／憑什麼

### #4 head

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/front.webp

依 prompt.txt §3 Part 1 與 spec/object-sculpt-spec.json 的 head / hair-cap / hair-spikes /
hair-fringe / face-print / ear-l / ear-r / neck / choker 建 head，只做這個 part，不整合、不碰
其他 part 的檔案。髮刺照 reference 佈局擺，不准程序化散佈；臉是印刷 CanvasTexture，不建模眼球。
socket 原點 (0, 0.673, 0)。交付 parts/createHead.ts。
```

### #5 left shoulder

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/left.webp

依 prompt.txt §3 Part 2 建 deltoid-l + pauldron-l，只做這個 part。護肩是浮貼獨立殼，沿整條
三角肌邊界有可見縫隙線；背面接一片深橄欖三角形背帶斜跨肩胛。與右肩各自獨立，**不做鏡射**。
socket (+0.100, 0.660, 0)，出口 upperArm。交付 parts/createShoulderLeft.ts。
```

### #6 right shoulder

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/right.webp

依 prompt.txt §3 Part 3 建 deltoid-r，只做這個 part。純皮膚三角肌板，側視五邊形，無袖無罩，
突出於軀幹且寬於下方上臂。socket (-0.100, 0.660, 0)，出口 upperArm。
交付 parts/createShoulderRight.ts。
```

### #7 上臂（左右同形，唯一可鏡射的一對）

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/left.webp

依 prompt.txt §3 Part 4/5 建 upper-arm，只做這個 part。窄皮膚方棒、角倒角，明顯細於上方三角肌
與下方前臂；側視前傾 10–15°、正視外展 8°，長度 0.115。socket 肩端，出口 elbow。
交付 parts/createUpperArm.ts（吃一個 side 參數做左右）。
```

### #8 left front arm

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/left.webp

依 prompt.txt §3 Part 6 建 forearm-l + bracer-l + fist-l，只做這個 part。前臂是向下加寬的
錐形板，向前向內折使拳頭落在髖線之前——肘前折是 pose 簽名，垂直手臂即不合格。灰護腕高約 0.045、
下緣在側視微微外懸；拳是單一倒角立方體，無手指。socket 肘，出口 fist。
交付 parts/createFrontArmLeft.ts。
```

### #9 right front arm

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/right.webp

依 prompt.txt §3 Part 7 建 forearm-r + fist-r，只做這個 part。同左前臂的錐形板與肘前折，但皮膚
前臂直接以平切硬接縫接黑色拳，**沒有灰護腕段**。socket 肘，出口 fist。
交付 parts/createFrontArmRight.ts。
```

### #10 body

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/front.webp

依 prompt.txt §3 Part 8 建 torso + strap-l + strap-r + strap-back + belt，只做這個 part。
扁平多面板 0.673→0.513，寬深比 2.2:1（硬閘門）。背帶是有厚度階差的凸起條不是彩繪，越過肩線
延伸到背面成斜三角板；腰帶高 0.033 環繞一圈，是軀幹最寬處。socket (0, 0.513, 0)，
出口 neck / shoulderL / shoulderR / hip。交付 parts/createBody.ts。
```

### #11 legs（最難，決定剪影）

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/left.webp

依 prompt.txt §3 Part 9 建 legs + hip-yoke + leg-l + leg-r，只做這個 part。**單一連續體積，
不是兩條褲管。** 三件事會被閘門盯著：臀部最寬 0.278 要大於肩寬 0.200；側面必須是前後帶尖的
菱形、最大深 0.142 在 Y=0.335；襠部倒 V 拱頂在 0.268。yoke 前後都有下尖 V、尖端 0.435、
凸出有階差。socket (0, 0.513, 0)，出口 ankleL/ankleR (±0.055, 0.173, 0)。
交付 parts/createLegs.ts。
```

### #12 shoes

```
/img2threejs src/assets/exhibits/ff7-cloud-strife-polygon-figure/left.webp

依 prompt.txt §3 Part 10 建 boot-cuff + sole，兩腳一起做、鏡射，只做這個 part。鞋底是等厚
0.055 的平板楔不是曲面鞋底，總長 0.148 其中約 ⅔ 在踝前、後跟很短，頂面自靴筒下方外伸成乾淨檐口，
趾端鈍倒角。俯視外撇 25–30°，**不平行**。socket 踝頂中心。交付 parts/createShoes.ts。
```

---

## Stage 1 驗收（task #13）

每個 part 都要跑完這四步才算過。`<PART>` 換成 part id，`<SHOT>` 換成 render 路徑。

```bash
cd $SKILL

# 1. Tier 1，並寫回 spec
python3 forge/stage4_review/diagnose_render.py <SHOT> \
  --spec <spec 路徑> --pass-id blockout --in-place

# 2. 非平面形都要多角度：固定視角 + 至少兩個 orbit
python3 forge/stage4_review/diagnose_render_multi_angle.py <SHOT> <ORBIT1> <ORBIT2>

# 3. 併圖後用 agent vision 看，**≥6× NEAREST，未放大不算看過**
python3 forge/stage4_review/make_comparison_sheet.py \
  --reference <對應 reference 或 crop> --render <SHOT> --out cmp-<PART>.png --json

# 4. 記分
python3 forge/stage4_review/append_review.py <spec 路徑> \
  --pass-id blockout --fidelity <0-1> --action <continue|refine-spec|refine-code|request-input|stop> \
  --summary "..." --render-screenshot <SHOT> --comparison-image cmp-<PART>.png \
  --ai-vision-score <0-1> --layer-scores-json '{...}' --feature-reviews-json <f.json> --in-place
```

任一識別特徵錯就是失敗，即使總分過：**handedness、臀部菱形側面、肘前折、髮刺佈局、鞋底楔形**。
另外檢查 flatShading 沒被磨掉、part 自己可 explode 可 click。

修正預算 3/pass、6/total，到頂即硬停。

---

## Stage 2 — 整合（task #14）

十個 part 全過才開始。

```
依 prompt.txt §5 整合十個 part 成 createCloudStrifePolygonFigureModel.ts。
**這個檔案不准寫任何幾何**——只做 socket 擺放與 pose 旋轉；要改形狀就回 part 檔改。
Pose：上臂外展 8°／前傾 12°、前臂肘前折使拳頭落在髖線前且高度 0.400–0.450、雙腳 yaw ±27°、
頭部平視、雙腳平踩 Y=0。常數所有權：整合檔只擁有 socket 位置與 pose 旋轉。
```

整體閘門：

```bash
cd $SKILL && python3 forge/stage4_review/check_part_coverage.py \
  --spec <spec 路徑> --manifest parts.json
```

外加對四個正投影視角（front / back / left / right）做 silhouette IoU，以及整尊 explode / click。

---

## Stage 2 — 接線收尾（task #15）

站台已經接好了，這一步只剩兩件事：

1. 把 `src/pages/ff7-cloud-strife-polygon-figure/index.vue` 裡的 placeholder `mount` 換成真的 viewer
   （`mountCloudStrifeViewer`，放 `src/utils/`，因為首頁 hero 也會用），
   並在 `src/utils/exhibits.ts` 把 `status` 改 `done`、`liveModel` 改 `true`、補 `modelVersion`。
2. 在 `src/components/home/heroStage.ts` 的 `heroEntries()` 補一筆，首頁轉盤才會轉到它。
3. 寫 `spec/RELATIONSHIPS.md`：十個 part、socket、管線順序、各 part 擁有哪些常數。

已完成的接線（不用重做）：`content/exhibits/ff7-cloud-strife-polygon-figure.yml`、
`src/utils/exhibits.ts` 條目、`src/utils/exhibitSlugs.ts`、
`src/pages/ff7-cloud-strife-polygon-figure/index.vue`（頁面即路由，沒有 map 要註冊）、
`src/RootApp.vue` 的 FF7 主題路由、圖與 prompt 統一走 `src/utils/exhibitAssets.ts`。

驗證：

```bash
npx velite build && pnpm build
```

---

## 環境備忘

- forge 讀像素的腳本原生只吃 PNG，但都有 macOS `sips` fallback，**webp 可以直接餵**。
- 但 **indexed-palette PNG 不行**。ImageMagick 對低色數圖會自動轉 palette，切 crop 時要加
  `-type TrueColor`，否則腳本會失敗。
- 放大看圖一律 `-filter point`（NEAREST），不要用預設的平滑縮放。
