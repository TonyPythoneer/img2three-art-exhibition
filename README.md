# img2three Art Exhibition

一個靜態展覽站，收錄以 `img2threejs` skill 從**單張參考圖**重建出來的程序化 Three.js 模型。每個展件都保留完整的 prompt、參考素材，以及決定成敗的那幾個判斷，當作技術紀錄而不是作品集。

## 技術棧

Vue 3 + vite-plus + vite-ssg（靜態預渲染）+ Tailwind 4，套件以 pnpm catalog 管理，部署到 GitHub Pages。

## 開發

```bash
pnpm install
pnpm dev      # http://localhost:3000
pnpm build    # 產生 dist/
```

## 新增一個展件

1. 建立 `src/exhibits/<slug>/`，放進參考圖（`.png`）與 `prompt-v1.txt`，需要的話再加 grilling 筆記之類的 `.md`。
2. 在 `src/exhibits/index.ts` 的 `exhibits` 陣列補一筆資料，填上 `slug`、`title`、`images`、`promptFile`、`decisions` 等欄位。

`src/exhibits/index.ts` 是純資料，`vite.config.ts` 會直接 import 它來產生 SSG 路由，所以這個檔案不要放任何 asset import 或 `import.meta.glob`。圖片與 prompt 內容由頁面元件用 glob 解析成實際 URL。

## 版權

站內的參考圖版權屬於原權利人（Balamb Garden 為 Square Enix 所有）。此處僅作為程序化重建的技術研究與紀錄用途，非商業使用。

## 交接

新 session 接手請先讀 [HANDOFF.md](HANDOFF.md)。它記錄目前的閘門狀態、下一步的優先序、絕對不要動的東西、以及已經被量測否決不要重試的假設。
