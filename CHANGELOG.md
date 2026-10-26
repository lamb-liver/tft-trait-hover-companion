# Changelog

## 0.4.6 — 2026-10-26
- 羈絆欄：基本搜尋只認到 1–2 個徽章時，逐列往上下找其餘的列；480p 等低解析度實況隔列漏認時，用兩個徽章距離的一半推算列距。門檻仍為 0.72，且需領先第二名 0.10。/ Trait list: with only 1-2 badges found, walk the other rows one at a time; on low-res streams that miss every other row, use half the badge gap as row pitch. Threshold unchanged.
- 羈絆欄：放大裁切的實況（例如 1152×720、徽章較大且清單貼近左緣）不再整列被當成道具欄濾掉：徽章夠大（≥ 26/1080）時左界放寬到 33/1080。/ Zoomed streams whose larger badges sit left of the usual list bound are no longer dropped.
- 已選海克斯強化沿用、黑邊裁切等見 0.4.5。驗證：未參與調整的 307 張 heldout 截圖羈絆召回 0.957 → 0.991，誤認 0；702 張回歸 0 張遺失。/ Held-out recall 0.957 → 0.991, 0 wrong; 702-frame regression lost 0.

## 0.4.5 — 2026-10-26
- 已選海克斯強化：畫面沒變時沿用上次讀到的名稱，現在最多沿用 10 秒（每次重新讀到同一組會重新計時），黑邊裁切範圍改變時立刻清掉，不會把舊位置的提示畫到新位置。門檻仍為 0.72／0.80。/ Selected-augment hold now expires 10 s after the last confirming read and is dropped when the letterbox crop changes. Thresholds unchanged.
- 黑邊：畫面沒變的判斷改看裁切後的圖。比對程式與資料與 0.4.4 相同。/ Unchanged-HUD check signs the cropped picture. Matcher and data same as 0.4.4.

## 0.4.4 — 2026-10-25
- 商店簡短說明（manifest description）改為：看聯盟戰棋實況忘了羈絆或海克斯強化的效果？滑鼠移到圖示上就顯示說明。畫面只在瀏覽器內處理。/ Store summary updated.
- 設定頁與隱私權政策用語統一為「海克斯強化」「效果說明」。比對程式與資料與 0.4.3 相同。/ Wording only; matcher and data same as 0.4.3.

## 0.4.3 — 2026-10-25
- 羈絆欄：圖示畫得比清單中位數大的徽章（1 個單位就啟動的獨特羈絆、部分金色徽章、介面縮放較大的實況）不再漏認：羈絆比對多一個 56 px 尺寸；空列多試大 8／12 px；清單頂端或底端連續多列沒認到時，逐列往外找（最多 4 列）。門檻仍為 0.72。/ Trait list: badges whose glyph is drawn larger than the list median (1-unit unique traits, some gold badges, larger HUD scale) are no longer missed: one more trait scale (56 px), empty rows also try +8/+12 px, and the edge search walks outward row by row (up to 4). Threshold unchanged (0.72).
- 海克斯強化：「開局新手包」(Build A Bud) 改用遊戲實際畫的鐵砧圖示（CDragon 15.20 buildabud_iii），不再誤認為「活火爐」。/ Build A Bud uses the anvil art the game draws (CDragon 15.20 buildabud_iii); no longer read as Living Forge.
- 速度：56 px 只在基本尺寸看到部分清單（1–2 個徽章，或徽章在 48／64 px）時才補找，且只在清單真的含 56 px 徽章時沿用；海克斯強化卡位在 1/4 縮圖最高分低於 0.60 時直接跳過。/ Speed: 56 px is searched only when the base scales see part of a list, and kept only when the list uses it; augment card regions whose 1/4-scale best score is below 0.60 are skipped.
- 海克斯強化資料：移除 196 個 S18 已改用 DA_ 新版的舊版 ID：190 個和 CDragon 16.21 TFTSet18 裡的 DA_ 同英文名稱，6 個的 DA_ 新版見於 tactics.tools S18 資料。/ Augments: dropped 196 legacy IDs replaced by DA_ augments in Set 18 (190 by name in CDragon 16.21, 6 per tactics.tools S18 data).
- 設定頁加上作者與問題回報連結；隱私權政策連結改指向公開的 companion repo。/ Options page: author and issue links; privacy link points to the public companion repo.

## 0.4.2 — 2026-10-25
- 省電：分頁在背景、影片暫停、滑鼠離開播放器一段時間時暫停比對；羈絆欄與海克斯強化區沒變時沿用結果；依每幀耗時自動拉長間隔。設定頁新增「省電模式」。/ Scans only when needed; reuses results when the HUD is unchanged; adaptive interval; new power-saving mode.
- 提示框：海克斯強化階段無法判斷時明確標示「階段無法判斷」並列出各階段效果，不猜測。/ Clear "tier unknown" label; tiers are never guessed.
- 穩健性：實況版面把遊戲縮在黑邊裡時，自動裁掉黑邊再比對（測試召回 84% → 99.7%，誤判 7 → 0）。/ Auto-crops black bars around a shrunken game picture.
- 新增「回報辨識錯誤」按鈕：把畫面與辨識結果存成本機檔案，不上傳。/ "Report wrong result" saves a local file; nothing is uploaded.

## 0.4.1 — 2026-10-24
- 擴充功能名稱改為「TFT羈絆提示」；介面與文件用語統一為臺灣繁體中文（擴充功能、實況主、聯盟戰棋）。比對程式與資料與 0.4.0 完全相同。/ Renamed to TFT羈絆提示; Taiwan Traditional Chinese wording. Matcher unchanged.

## 0.4.0 — 2026-10-24
- 純 Chrome 擴充功能：比對改在瀏覽器內以 OpenCV（WebAssembly，無 eval）執行，不再需要 Python 本機程式。/ Pure Chrome extension: matching runs in-browser (OpenCV WebAssembly, no eval); the Python companion is now optional.
- 新增左上角已選海克斯強化欄辨識，依欄位位置判斷 +／++ 版本；銀色／金色／彩色命運多出的一個選擇也會計入。/ Picked-augment bar recognition with tier inference from slot position, including the extra pick from Destiny augments.
- 補上 42 個海克斯強化的實際圖示。/ Real icons for 42 more augments.
- 效能：每幀約 0.9 秒降到 0.77 秒。/ Per-frame time ~0.9 s → 0.77 s.
- 已送 Chrome 線上應用程式商店審核（不公開項目）。/ Submitted to the Chrome Web Store (unlisted).
- 授權：程式碼 MIT；附 OpenCV Apache-2.0、Emscripten 授權。/ MIT license; OpenCV and Emscripten notices bundled.
