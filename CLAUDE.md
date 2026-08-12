# img2three 展覽站

用 img2threejs skill 把參考圖重建成純程式 Three.js 模型的展覽站。**一個展品 = 一條 route =
一個 `src/pages/<slug>/index.vue`**，接線方式與管線順序見各展品
`artifacts/exhibits/<assetDir>/spec/RELATIONSHIPS.md`。

## 建模

- 接合處放大 6–8×（NEAREST）逐點看。原尺寸 crop 不算看過；crop 按**接合處**切，不按材質切。
- 未放大不得宣稱「解析不出來」。放大後仍不行 → 寫「放大 N× 後仍無法判讀」並附圖。
- 判讀不出的部位一律進**猜測清單**（部位／兩種讀法／選了哪個／憑什麼）：第一則回覆就給，交付時隨模型再交。
- 使用者不在時不准卡住：給預設往下做，講明「我讀成 X，也可能是 Y，先照 X，要改說一聲」。
- 用圖不用字：藍本放大圖與 render 並排。
- 讀法與規格衝突 → 照規格做但**明講**，不要用「看不出來」蓋過去。
- 驗收 = 機械閘門（斷言、silhouette IoU、part coverage）+ 放大後的原圖比對。
- 每個數字只追溯到 `artifacts/` 產物，不抄自己的摘要或另一份文件（`spec/audit_records.py` 擋）。

## 新增展品要接五個地方

少接一個首頁就看不到：

1. `src/pages/<slug>/index.vue` — 展品頁本身，第一行呼叫 `useExhibit("<slug>")`。
   route 是檔案位置生的，沒有 map 要註冊。
2. `src/utils/exhibits.ts` 條目
3. `src/utils/exhibitSlugs.ts` 補 slug（`vite.config.ts` 的 `includedRoutes` 讀這支，
   是 allowlist 不是 filter，沒補就不會 prerender）
4. `src/components/home/heroStage.ts` 的 `heroEntries()`
5. `content/exhibits/<assetDir>.yml`（velite 管的文案與 `images[]`）＋
   `src/assets/exhibits/<assetDir>/` 底下的圖與 `prompt.txt`

目錄規則（Nuxt 的 `app/` 分法，`src/` 為根）：

- `src/pages/` **就是 URL 表面**，一個 `.vue` 一條 route。plugin 只掃 `.vue`，但別靠這點
  往裡塞東西 — 多放一個 `.vue` 就多一條垃圾 route。
- `src/composables/` 反應式的取用（`useExhibit`）；`src/utils/` 純函式與資料
  （展品登錄檔、part inspector、幾何工廠）。幾何工廠放這裡是因為首頁 hero 和
  `ultima-v2-harness` 也在用，放進 page 目錄會變成 component 反向 import page。
- **頁面資源**（`images[]` 列的圖、`prompt.txt`）→ `src/assets/exhibits/<assetDir>/`，
  平放不要開子資料夾。Vite 會 hash 並自動套 `base`。
- **閘門證據**（`spec/`、`brief/`、`.img2threejs/`）→ `artifacts/exhibits/<assetDir>/`，
  永遠不進 bundle。只留**量測記錄與產生它的腳本**：JSON、`.py`/`.sh`/`.mjs`、`.md`。
- **render、zoom 比對圖、PBR map、detail-inventory crop 不留**。它們都能用旁邊的
  `capture_*.sh`／`tools/capture_*.mjs` 從程式重跑出來，數字本身在 JSON 裡。要比對就當場產、
  看完就丟。`artifacts/` 唯一保留的圖是**不可再生的來源圖**：`references/` 的藍本與
  `assets/` 的藝術圖 crop。
- 圖與 prompt 一律走 `src/utils/exhibitAssets.ts`，不要在元件裡自己開 `import.meta.glob`。
  glob 一律用 `*/` 不要用 `**/`：`**` 會把整包閘門證據 eager 打包進 client bundle。
