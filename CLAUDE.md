# img2three 展覽站

用 img2threejs skill 把參考圖重建成純程式 Three.js 模型的展覽站。每個展品是
`src/exhibits/<slug>/`，接線方式與管線順序見各展品 `spec/RELATIONSHIPS.md`。

## 建模

- 接合處放大 6–8×（NEAREST）逐點看。原尺寸 crop 不算看過；crop 按**接合處**切，不按材質切。
- 未放大不得宣稱「解析不出來」。放大後仍不行 → 寫「放大 N× 後仍無法判讀」並附圖。
- 判讀不出的部位一律進**猜測清單**（部位／兩種讀法／選了哪個／憑什麼）：第一則回覆就給，交付時隨模型再交。
- 使用者不在時不准卡住：給預設往下做，講明「我讀成 X，也可能是 Y，先照 X，要改說一聲」。
- 用圖不用字：藍本放大圖與 render 並排。
- 讀法與規格衝突 → 照規格做但**明講**，不要用「看不出來」蓋過去。
- 驗收 = 機械閘門（斷言、silhouette IoU、part coverage）+ 放大後的原圖比對。
- 每個數字只追溯到 `artifacts/` 產物，不抄自己的摘要或另一份文件（`spec/audit_records.py` 擋）。

## 新增展品要接四個地方

少接一個首頁就看不到：`src/exhibits/index.ts` 條目（route 由 `vite.config.ts` 的
`includedRoutes` 從這裡生）、`src/pages/[slug].vue` 的 `STAGES` map、
`src/components/home/heroStage.ts` 的 `heroEntries()`、以及 **exhibit 根目錄**的
`*.png` 與 `prompt.txt`（glob 只掃直接子檔，放在子資料夾的圖不會被撿到）。
