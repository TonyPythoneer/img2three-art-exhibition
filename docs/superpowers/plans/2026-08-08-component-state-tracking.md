# 組件狀態：一張產生出來的表，取代散在六份文件裡的零件資訊

問題不是「沒有記錄」，是記錄太多份、而且沒有一份回答得了問題。

## 1. 為什麼

「`spinnerEndLeft` 現在是什麼狀態」目前要讀六個地方：factory 的 JSDoc 散文（形狀怎麼來）、
`confidence-report.md`（信心值）、`CURRENT-MODEL.md` §11 與 `image-analysis.md`（未決問題 G/U）、
`check_centerline.py` ＋ `audit_records.py` 的程式碼（動它會炸什麼）、`parts.json`（實際尺寸）。
「哪些常數被使用者鎖死」則**完全沒有檔案記錄**，只存在於對話裡。

六份會各自漂，這一輪已經抓到：信心表三列跟 spec 不合、§4 的 socket 世界座標停在兩輪前、
spec 裡 10 個 `parentSocket` 指向不存在的 socket。

todo 追的是**我的任務**不是**模型的狀態** —— 跑完 21 個任務只知道「#18 完成」，
回答不了「`CONNECTOR_ROOT` 誰在哪天鎖的」「IoU 從 0.8553 掉到 0.8175 是哪條指令造成的」。

## 2. 提案：`spec/component-state.md`，一行一個零件，**產生的不是手寫的**

| 欄位           | 值                                                | 從哪產生                                                        |
| -------------- | ------------------------------------------------- | --------------------------------------------------------------- |
| **provenance** | `measured` / `derived:<來源>` / `directed:<日期>` | factory 常數的 `@provenance` 標記                               |
| **locked**     | 凍結它的指令，空白 = 可動                         | factory 的 `@locked <日期> <一句話>`                            |
| **guarded**    | 動它會觸發的斷言                                  | grep `check_centerline.py` / `audit_records.py` 裡的零件名      |
| **open**       | 未決問題編號（G/U），空白 = 沒有                  | `CURRENT-MODEL.md` §11 與 `image-analysis.md`，每則強制標註零件 |

```
spinnerEndLeft
  provenance  derived:spinnerSeat() + measured:artwork taper (RMS 0.57 px)
  locked      —
  guarded     mirror-pair, exposed-flare<=2.0, shoulder-monotonic, seat-burial
  open        G-spinner-base(平底或鈍截), G-taper(保角度或保半徑)

leatherConnectorRight
  provenance  derived:CLAMP_OUTLINE[2] + R*(-sin a, cos a); length=垂足投影
  locked      2026-08-07 ROOT/ANGLE/RADIUS 由使用者定死
  guarded     #17-root, #17-rake, #17-cap-flush, handover, daylight
  open        G4(藍本臂端離射線 28.947，任何長度構不到)
```

**一定要「產生」**：repo 已經有 `audit_records.py` 在擋數字漂移，理由是「文件引用文件就是漂移的開始」。
手寫的狀態表三輪之內一定跟現實脫節 —— 前面六份就是這樣壞掉的。

**新增的作者負擔只有一項**：在 factory 常數上加兩行標記。其餘三欄都是抽既有的東西。

```ts
/**
 * @provenance directed:2026-08-07  使用者手繪圖 references/04-user-sketch-guard.png
 * @locked     2026-08-07  臂根＝clamp 外下角＋法線一個半徑；不得移動
 */
const CONNECTOR_ROOT: [number, number] = [46.1481047, 23.4126631];
```

## 3. 進度追蹤 = 這張表的 diff

一條指令進來只會做三件事之一：**確認**量測（provenance 不變，信心上升）、
**覆寫**量測（`measured` → `directed:<日期>`，量測值保留為證據）、
**開啟衝突**（`open` 多一則，附衝突量，例如「差 28.947 單位」）。

所以「這一輪做了什麼」= `git diff spec/component-state.md`。比 todo 精準，而且不可能說謊。

## 4. 要刪掉什麼

只加不刪就只是多第七份文件。

| 現有                                     | 處置                                                             |
| ---------------------------------------- | ---------------------------------------------------------------- |
| `confidence-report.md` 的**每零件表**    | 刪掉，改由本表產生。散文分析（衝突 1–7）保留                     |
| `CURRENT-MODEL.md` §11 猜測清單          | 保留散文，每則**強制標註零件**，由表引用                         |
| `CURRENT-MODEL.md` §4 圖裡的 socket 座標 | 刪掉座標數字改引 `object-sculpt-spec.json`；圖保留（拓樸不會漂） |
| `audit_records.py` 退役清單              | **保留不動**。那是防漂網，不是狀態                               |

淨結果：六份降到三份 ＋ 一張產生的表。

## 5. 落地步驟

1. `spec/component_state.py` — 讀 factory 標記 ＋ `parts.json` ＋ grep 兩支斷言腳本，輸出 `component-state.md`；
   同一支腳本裡直接斷言，違反就 exit 1：
   - `parts.json` 的每個零件在表上**各出現剛好一次**
   - 每則 G/U 都指向存在的零件
   - 每個 `directed` 都有日期與出處（防止「指定」變成無主的魔術數字）
2. 補齊 factory 的 `@provenance` / `@locked` —— 這一輪的對話就是資料來源
3. 接進 `run_gates.sh`（放在 `audit_records.py` 那段旁邊）
4. 用**造假資料**夾過：漏一個零件、G 指向不存在的零件、`directed` 沒日期 → 三個都要 FAIL
5. 刪掉 §4 那三處被取代的內容

## 6. 不做什麼

- **不做 `component-state.json`。** 沒有第二個消費者；閘門就在產生器裡跑。真的出現機器讀者再加。
- **不改兩支斷言腳本。** `guarded` 用 grep 零件名推出來。天花板：斷言若動態組零件名會 grep 不到 ——
  到那天才讓它自己輸出「我守著誰」。
- **不做 UI、不做 dashboard。** 一個 `.md`，`git diff` 就是介面。
- **不追每次 render 的數字。** 那是 `artifacts/` 與退役清單的工作；本表只記狀態（來源、鎖定、守衛、未決）。
- **不改 `brief/`。** 那是上游供稿。
