# 中文主 Prompt（英文版完整對照）

以下內容可直接交給主要實作 Agent。結構與英文版相同，方便逐段檢查英文 prompt 的真正要求。

---

## PROMPT 開始

你是負責幾何規格、subagents 分工與整合的主 Agent。目標是根據 `references/01-authority-artwork.webp`，忠實重建 **Final Fantasy VII Ultima Weapon** 的 Three.js 模型。單獨切出的權威劍圖位於 `assets/artwork-sword-crop.webp`。

你的任務不是重新設計一把新劍，而是把 artwork 轉成明確的零件階層，讓 subagents 可以各自工作，最後依固定接口組裝並與 artwork 驗證。

### 1. 從真正的 img2threejs skill 流程開始

本文件已對照 img2threejs `SKILL.md` 1.4.4。實際執行時仍以目前 checkout 的 repository 為準。

1. 第一次先初始化 generic profile 的續作狀態：

```bash
python3 forge/state.py init \
  --state .img2threejs/state.json \
  --reference assets/artwork-sword-crop.webp \
  --profile generic
```

2. 每次開始、恢復工作或進入修正 loop 前，都先執行：

```bash
python3 forge/next.py --state .img2threejs/state.json
```

3. 遇到 hard stop 或 exit code `3` 必須停止，不可依賴聊天記憶猜測進度。
4. 使用 repository 真正的 `ObjectSculptSpec`、`detailInventory`、`qualityContract`、repetition systems、sockets、materials、review history，以及 TypeScript `THREE.Group` factory。
5. 一律使用目前版本實際存在的 schema、檔案路徑、指令、pass lock 和輸出格式，不可虛構 repository 內部結構。
6. 遵守原有專案模式，並讓每個零件可以獨立 review。

### 2. 參考圖片權限順序

| 優先級 | 參考檔                                                | 可以用來判斷的內容                                         |
| -----: | ----------------------------------------------------- | ---------------------------------------------------------- |
|      1 | `references/01-authority-artwork.webp` 與兩個劍身切圖 | 權威輪廓、比例、零件數量、重疊方式、顏色位置與低多邊形風格 |
|      2 | `references/03-community-colored-model.webp`          | 只有 artwork 看不到的厚度與切面提示                        |
|      3 | `references/02-community-draft.webp`                  | 只有粗略拓樸與接合提示                                     |

任何參考資料與 artwork 衝突時，都以 artwork 為準。

### 3. 不可更改的群組階層

```text
SwordRoot
├── BladeGroup（劍身群組）
│   ├── outerCrystalShell（透明外層水晶劍身）
│   ├── purpleEnergyInsert（紫色漸層內層）
│   ├── darkCoreTriangle（深色小三角形）
│   └── rootDiamondGem（根部菱形寶石）
└── HiltGroup（劍柄群組）
    ├── guardCore（護手核心與兩側承載器）
    ├── driverArray（四個驅動器）
    │   ├── driver01_left_upper
    │   ├── driver02_left_lower
    │   ├── driver03_right_upper
    │   └── driver04_right_lower
    ├── leatherTGrip（皮革 T 形劍柄）
    └── metalSpinnerPommel（金屬陀螺形尾端）
```

劍身固定是 **四個零件**。劍柄固定是 **四種零件**。`driverArray` 裡固定有四個驅動器，左右各兩個。

### 4. 零件描述表

#### BladeGroup／劍身群組

| 群組       | 零件名稱                             | 數量 | 顏色：純色／漸層／色碼                                                                     | 材質                                                                               | 零件本身的描述                                                                                                                                                                                                                                                                                                                               |
| ---------- | ------------------------------------ | ---: | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BladeGroup | `outerCrystalShell` 透明外層水晶劍身 |    1 | 淡白至淡紫的半透明漸層。高光 `#F8F8FF`；主色 `#E4E5F3`；陰面 `#B8BBD6`；冷色邊緣 `#D7D9EE` | 非金屬、低粗糙度、切面式水晶；控制透明度或 transmission；使用 flat/faceted shading | 這是經典的外層大劍身。外形像細長葉片或矛頭：頂端尖銳，上半部較窄，下半部較寬並包住劍根。它在四周都必須明顯大於紫色內層。**外層白色水晶外殼需要開鋒**：劍尖要收成明確尖點，左右兩側也要明顯往刀鋒邊緣變薄，從劍尖往下看要有「中心較厚、往側邊收縮」的刀身感，而不是鈍厚板。截面要淺且有中央稜線，不可做成平面卡片，也不可做成厚重圓滑的大刀。 |
| BladeGroup | `purpleEnergyInsert` 紫色漸層內層    |    1 | 垂直深紫到亮紫漸層。尖端 `#19106E`；上段 `#2B168F`；中段 `#4822C0`；下段亮紫 `#7C3CFF`     | 能量水晶；不透明到輕微半透明；少量 emissive；保留切面                              | 一個嵌入外層劍身的內部劍片。最上端是小三角尖端；往下後兩側逐漸展開，形成長形、向劍柄方向加寬的梯形。它停在根部寶石後方或上方，不可到達外層劍尖，也不可填滿整個外層水晶。**內部水晶不需要開鋒**，不可做成像外層刀鋒那樣的銳利刀口；它應維持為有切面的內嵌晶體量體。                                                                           |
| BladeGroup | `darkCoreTriangle` 深色小三角形      |    1 | 以深紫／暗酒紅為主的近純色，小幅漸層。尖端 `#210A38`；主色 `#3A0B43`；下方切面 `#64123F`   | 密實、不透明、比紫色內層更暗的水晶                                                 | 位於紫色內層下段前方的狹窄三角形，尖端朝上並保持置中。它只是一個小三角形，不是第二把長劍，也不可向左右擴張成大型中央面板。                                                                                                                                                                                                                   |
| BladeGroup | `rootDiamondGem` 根部菱形寶石        |    1 | 紅紫水晶漸層。高光 `#FF3866`；主色 `#C0184D`；陰面 `#5A0B34`；深色切面 `#330820`           | 小型透明／切面寶石；細長菱形或低多邊形雙錐體                                       | 位於劍身根部、護手正前方的細長菱形水晶。上端會覆蓋深色小三角形，下端稍微跨入護手區域。必須看起來像有厚度和切面的寶石，不可只是平面的紅色箭頭。                                                                                                                                                                                               |

#### HiltGroup／劍柄群組

| 群組      | 零件名稱                            |             數量 | 顏色：純色／漸層／色碼                                                                   | 材質                               | 零件本身的描述                                                                                                                                                               |
| --------- | ----------------------------------- | ---------------: | ---------------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HiltGroup | `guardCore` 護手核心                | 1 組左右鏡像結構 | 低調純色與金屬明暗。炭黑 `#202126`；深鋼色 `#353640`；暗金 `#8D8450`；橄欖金 `#6F6A3D`   | 切面深色金屬，加上暗金／橄欖金金屬 | 包含中央劍身插槽和左右兩個承載器。兩側結構向外、向下傾斜，尾端各有一個小型暗金切面配重。整體要小而機械化，左右承載器必須保持狹窄、傾斜，並在視覺上從屬於主劍身與四個驅動器。 |
| HiltGroup | `driverArray` 四個驅動器            |                4 | 酒紅／紅紫色細桿，帶深色邊緣和小面積高光。主色 `#7C102F`；高光 `#BB2A50`；陰影 `#2E0716` | 狹長的切面金屬桿或能量導體         | 固定四個：左邊兩個、右邊兩個，左右鏡像。它們從護手向外並略微向上放射。形狀是細長的矩形或切面桿，不是六片扇葉、不是大量尖刺，也不是厚重立方體。                               |
| HiltGroup | `leatherTGrip` 皮革 T 形劍柄        |                1 | 接近黑色、只有細微明暗。底色 `#111216`；纏繞凸起 `#292A30`；邊緣 `#3B3C43`               | 粗糙皮革或皮革包覆；非金屬         | 護手下方的一根筆直、狹窄握柄。整把劍的護手加握柄輪廓看起來像 T，不是額外增加一根真正的 T 形橫桿。握柄可稍微收窄，保留切面，加入克制的纏繞紋或螺旋帶。                        |
| HiltGroup | `metalSpinnerPommel` 金屬陀螺形尾端 |                1 | 暗金金屬漸層。高光 `#B8A45C`；主色 `#958044`；陰影 `#5E512D`                             | 切面金屬                           | 位於握柄正下方的小型尖尾，形狀像緊湊的陀螺或圓錐。它比握柄窄，且要明顯呈現金屬感。不可做成大圓球或過度華麗的裝飾。                                                           |

### 5. 統一座標與初始比例

模型本身先保持直立：

- `+Y`：從護手指向劍尖。
- `-Y`：從護手指向劍柄尾端。
- `+Z`：artwork 中看到的正面。
- `X`：護手左右方向。
- `guard_center_anchor = (0, 0, 0)`。

先把整體長度標準化為 `1000` 單位：

| 尺寸                     |  初始目標 |
| ------------------------ | --------: |
| 外層劍尖到護手中心       |     `760` |
| 護手中心到握柄／尾端接口 |     `205` |
| 尾端延伸                 |      `35` |
| 外層劍身最大寬度         | `175–190` |
| 紫色內層最大寬度         |  `85–105` |
| 包含驅動器的護手總寬度   | `330–370` |
| 外層劍身最大厚度         |   `22–32` |
| 護手最大厚度             |   `35–50` |
| 握柄寬度                 |   `24–32` |

這些只是 blockout 的共同起點。後續必須用 artwork 疊圖調整，不可把表格數字當成比圖片更高的權威。

外層水晶只需要少量但有意義的截面與縱向稜線。截面必須從中央稜線向左右刀鋒逐步收薄，劍尖也要收成明確尖點，讓外殼看起來有開鋒。不可使用圓滑膠囊形截面、整塊等厚的板狀厚度，或鈍掉的前端。相對地，紫色內層應保持較鈍、較有量體的切面水晶，不要套用同樣的刀鋒倒角。風格要保留 PlayStation 時代的低多邊形視覺。

### 6. Subagents 分工

1. **權威測量 Agent**：只量 artwork 的座標、landmarks 和比例，不做模型。
2. **外層水晶 Agent**：只負責 `outerCrystalShell`。
3. **紫色內層 Agent**：只負責 `purpleEnergyInsert`。
4. **核心與寶石 Agent**：負責 `darkCoreTriangle` 和 `rootDiamondGem`，但必須輸出為兩個獨立 node。
5. **護手 Agent**：只負責 `guardCore`。
6. **驅動器 Agent**：建立一份可重用的 driver geometry 與四個 transform，只負責 `driverArray`。
7. **握柄 Agent**：只負責 `leatherTGrip`。
8. **尾端 Agent**：只負責 `metalSpinnerPommel`。
9. **組裝 Agent**：只能調整 transform 與接合 adapter，不可暗中重做其他 Agent 的零件。
10. **驗證 Agent**：輸出固定視角、與 artwork 疊圖、回報誤差；不可直接修改 geometry。

每個建模 subagent 必須交付：

- node 名稱與 parent 名稱；
- local pivot；
- local bounding box；
- attachment anchors；
- material IDs；
- vertex／face 數量；
- 因為圖片看不到厚度而作出的假設；
- 白底與透明背景 preview。

### 7. Intake、spec 與 locked passes

使用 skill 強制的流程。真正的下一步與 pass 由 `forge/next.py` 決定。最低限度先執行：

```bash
python3 forge/stage1_intake/probe_image.py assets/artwork-sword-crop.webp

python3 forge/stage1_intake/build_detail_inventory.py \
  assets/artwork-sword-crop.webp \
  --mode grid-3x3 \
  --out-dir detail-inventory \
  --out detail-inventory.json

python3 forge/stage2_spec/new_pre_spec_assessment.py \
  "FF7 Ultima Weapon" \
  --image assets/artwork-sword-crop.webp \
  --complexity complex \
  --spec-query "faceted translucent crystal sword layered blade inset gemstone guard drivers leather grip" \
  --out assessment.json

python3 forge/stage2_spec/new_sculpt_spec.py \
  "FF7 Ultima Weapon" \
  --image assets/artwork-sword-crop.webp \
  --assessment assessment.json \
  --out object-sculpt-spec.json

python3 forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json
python3 forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality
```

在 code generation 前，把 starter targets 換成這份 prompt 中真正的識別特徵。每個可見細節都要對應到 `component.localFeatures` 或 `material.localOverrides`，不可只寫在說明文字裡。

每個 locked pass 都先查看狀態，再產生當前允許的 factory：

```bash
python3 forge/stage3_build/orchestrate_passes.py status object-sculpt-spec.json
python3 forge/stage3_build/generate_threejs_factory.py \
  object-sculpt-spec.json \
  --out src/createUltimaWeaponModel.ts
```

在 repository 的 pass lock 內保留以下視覺邏輯順序：

1. artwork 權威測量；
2. blockout 輪廓；
3. structure／階層、pivot、sockets、repetition systems 與 attachments；
4. form 與切面；
5. material 區域與漸層；
6. lighting；
7. 需要時加入 interaction/runtime；
8. optimization。

每個 pass 都要 render 和比較。輪廓或零件數量錯誤時，不可先做材質美化。每輪必須記錄改了什麼、還有哪些不一致，以及 evidence 檔案位置。

### 8. 組裝接口

使用以下 anchors，或轉換成 repository schema 的等價名稱：

```text
outerCrystalShell.root_anchor      -> guardCore.blade_socket_anchor
purpleEnergyInsert.root_anchor     -> outerCrystalShell.inner_insert_anchor
darkCoreTriangle.base_anchor       -> outerCrystalShell.core_anchor
rootDiamondGem.center_anchor       -> guardCore.gem_mount_anchor
guardCore.grip_anchor              -> leatherTGrip.top_anchor
leatherTGrip.pommel_anchor         -> metalSpinnerPommel.top_anchor
guardCore.driver_anchor[0..3]      -> driverArray.driver[0..3].root_anchor
```

四個驅動器使用同一份 geometry 或 instancing。鏡像後必須保持正常的 face normals 與材質方向。

### 9. Artwork 疊圖與相機驗證

模型保持直立，再建立兩個固定驗證視角：

1. 正面 orthographic view：檢查對稱、階層與比例。
2. artwork-match view：使用輕微 3/4 角度與接近 artwork 的畫面傾斜。

artwork-match view 必須：

- 使用 orthographic camera 或很弱的透視；
- 白色背景；
- 左上方柔和光源，讓水晶切面可見；
- 不可使用會遮住輪廓的強 bloom；
- 對齊劍尖、護手中心、寶石中心、握柄軸與四個 driver 端點；
- 輸出 overlay 與 difference 圖。

對齊後的 review 目標：

- silhouette IoU `>= 0.90`；
- 劍尖、護手中心、寶石中心、握柄尾端與四個 driver 端點誤差，各自 `<= 圖片高度 2.5%`；
- 劍身／劍柄長度比例誤差 `<= 3%`；
- driver 數量固定為 `4`；
- 劍身零件數量固定為 `4`。

### 10. 正向收斂條件

只有在下列條件全部成立時，才接受這個重建結果：

- 整體輪廓與零件位置由權威 artwork 控制；
- 淡白色外層水晶呈現為淺薄、有開鋒、有切面的劍身外殼；
- 紫色內層保持較小、內嵌，而且明確不開鋒；
- 深色核心維持為置中的小型三角形；
- 根部寶石呈現有厚度的細長菱形水晶；
- 驅動器固定為四個，左右各兩個並互相鏡像；
- 護手保持緊湊、狹窄，並與劍身插槽形成清楚機械接合；
- 握柄呈現為狹窄的皮革包覆軸體；
- 尾端呈現為小型尖頭金屬陀螺；
- 保留 PS1 時期以平面與少量切面構成的 low-poly 語言；
- 八種公開零件在合體前都能獨立 review；
- 所有隱藏厚度推測都不能改變 artwork 正面的權威輪廓。

### 11. 最終交付

1. repository 原生的 object/component spec；
2. 每個獨立零件的 source，或最接近 repository 慣例的拆分；
3. 包含階層、材質、pivot、anchors、尺寸與假設的 manifest；
4. 正面、artwork-match、側面與 3/4 render；
5. 透明背景 render；
6. artwork overlay 與 difference 圖；
7. 驗證數值與簡短差異報告；
8. 顯示八種零件與四個 driver instance 的 exploded view；
9. `object-sculpt-spec.json`；
10. 回傳 `THREE.Group` 並公開 repository 標準 runtime nodes／sockets 的 `src/createUltimaWeaponModel.ts`；
11. 保留 `.img2threejs/state.json`、review history 與 comparison evidence。

若實際 repository 規則與此階層發生衝突，先停止並回報，不可默默改掉 artwork 定義。

## PROMPT 結束
