# Changelog

## 0.4.1 — 2026-10-24
- 擴充功能名稱改為「TFT羈絆提示」；介面與文件用語統一為臺灣繁體中文（擴充功能、實況主、聯盟戰棋）。比對程式與資料與 0.4.0 完全相同。/ Renamed to TFT羈絆提示; Taiwan Traditional Chinese wording. Matcher unchanged.

## 0.4.0 — 2026-10-24
- 純 Chrome 擴充功能：比對改在瀏覽器內以 OpenCV（WebAssembly，無 eval）執行，不再需要 Python 本機程式。/ Pure Chrome extension: matching runs in-browser (OpenCV WebAssembly, no eval); the Python companion is now optional.
- 新增左上角已選海克斯強化欄辨識，依欄位位置判斷 +／++ 版本；銀色／金色／彩色命運多出的一個選擇也會計入。/ Picked-augment bar recognition with tier inference from slot position, including the extra pick from Destiny augments.
- 補上 42 個海克斯強化的實際圖示。/ Real icons for 42 more augments.
- 效能：每幀約 0.9 秒降到 0.77 秒。/ Per-frame time ~0.9 s → 0.77 s.
- 已送 Chrome 線上應用程式商店審核（不公開項目）。/ Submitted to the Chrome Web Store (unlisted).
- 授權：程式碼 MIT；附 OpenCV Apache-2.0、Emscripten 授權。/ MIT license; OpenCV and Emscripten notices bundled.
