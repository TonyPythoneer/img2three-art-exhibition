# PBR 證據:萃取有跑、證據保留、地圖刻意不接線

這是 Fable 5 重跑(與第一次 Opus 重建獨立)的材質證據紀錄。

## 跑了什麼

七個材質各切一個 crop(`crops/`,每個都先目視確認落在正確部位;gold 第一刀偏到背景有重切),
依序跑 `analyze_texture.py`(finish 分類 + scalar)與 `extract_pbr_evidence.py`
(albedo/roughness/height/normal/AO 五張圖 + 信心值)。

| 材質 | 分類器判定 | 信心 |
|---|---|---|
| outerBladeShellMaterial | painted-metal | 0.837 |
| purpleCoreMaterial | painted-metal | 0.86 |
| magentaSpineMaterial | painted-metal | 0.78 |
| crimsonEmitterMaterial | gem-metal | 0.86 |
| gunmetalGuardMaterial | painted-metal | 0.86 |
| agedGoldMaterial | brushed-steel | 0.86 |
| gripMaterial | brushed-steel | 0.794 |

信心全數 ≥ 0.7 門檻,referencePbr 證據區塊完整保留在 spec 內。

## 為什麼 scalar 被覆寫(逐筆記錄在各材質的 `finishClassifierOverride`)

分類器沒有「乳白半透明 PS1 殼」這個類別:它把外殼的 transmission 歸零、clearcoat 拉滿
——直接殺掉本重建的第一識別特徵(紫核透殼可見)。同理 grip/gold 被判成全金屬
(metalness 1.0、anisotropy 1.0),但平面著色的 PS1 資產沒有拉絲也沒有鏡面。
腳本做 enforcement、視覺判斷是 agent 的工作,所以 scalar 依觀察修正,證據原樣保留。

## 為什麼萃取出的 map 不接線(`roughness.map.wired = false`)

1. 來源是 146×292 的平面著色資產:色塊內部完全平坦,萃取出的 normal/roughness 變化
   只編碼了輪廓的抗鋸齒階梯。接上去等於把像素鋸齒壓成表面凹凸。
2. three.js 的 roughnessMap 與 roughness scalar 是相乘關係,接圖會把實際粗糙度平方掉。
3. 這個模型的表面語言是「每個 facet 一個平面色階」,由幾何 + flat shading 承擔,
   不由貼圖承擔。

結論與第一次重建相同,但是獨立得出;判斷依據是本次自己的 crop 與萃取輸出。
