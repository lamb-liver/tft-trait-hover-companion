# TFT羈絆提示（TFT Trait Hover）

[English](README.en.md) · [安裝說明](docs/install.md) · [隱私權政策](docs/privacy.md) · [更新紀錄](CHANGELOG.md)

看聯盟戰棋（TFT）實況時，常常忘記羈絆和海克斯強化的效果嗎？在 Twitch 直播或 YouTube 影片上，把滑鼠移到播放器畫面的羈絆或海克斯強化圖示，就會顯示繁體中文名稱與遊戲內的效果說明。

作者：羊肝（[lambliver.dev](https://lambliver.dev)）

- 0.4.0 起只要安裝 Chrome 擴充功能，**不用另外安裝 Python 或其他程式**。
- 辨識全部在你的瀏覽器裡執行，畫面不會上傳，也不收集任何資料。
- 只顯示遊戲內的名稱與敘述，不做推薦、不追蹤對手。

## 安裝

**Chrome 線上應用程式商店**：目前審核中，通過後會在這裡附上（不公開項目）連結，一鍵安裝並自動更新。

**搶先測試（手動載入，Mac／Windows 桌面版 Chrome）**：

1. 到 [Releases](https://github.com/lamb-liver/tft-trait-hover-companion/releases) 下載 `tft-trait-hover-0.4.3.zip`。
2. 解壓縮到一個固定的資料夾（之後不要刪除或搬移）。
3. Chrome 網址列輸入 `chrome://extensions`。
4. 開啟右上角「開發人員模式」。
5. 按「載入未封裝項目」，選擇解壓縮後含有 `manifest.json` 的那一層資料夾。

詳細步驟與疑難排解見 [docs/install.md](docs/install.md)。

## 使用

1. 打開正在玩聯盟戰棋的 Twitch 直播或 YouTube 影片。
2. 點工具列的「TFT羈絆提示」，或按 Alt+Shift+Y（Mac：Option+Shift+Y），角標出現「讀」就開始。
3. 滑鼠停在左側羈絆、海克斯強化選擇卡，或左上角已選的海克斯強化上，就會出現名稱與敘述。再點一次停止。

## 小功能

- **省電模式**：到擴充功能的設定頁勾選。比對間隔至少 3 秒，滑鼠離開播放器 20 秒就暫停。不開也會在分頁切到背景、影片暫停、滑鼠離開播放器 1 分鐘時自動暫停。
- **回報辨識錯誤**：讀取時播放器右上角的按鈕。會把當下畫面和辨識結果存成一個檔案到你的下載資料夾，不會自動上傳；要回報時把檔案附在 [Issues](https://github.com/lamb-liver/tft-trait-hover-companion/issues)。
- **階段無法判斷**：海克斯強化的 +／++ 版本圖示相同，無法判斷時提示框會標示「階段無法判斷」並列出各階段效果。

## 已知限制

- 不支援手機版聯盟戰棋的畫面；手機瀏覽器也無法安裝。
- 實況畫面上的韓文、日文等疊加圖層可能讓部分羈絆無法辨識，這時寧可不顯示。
- 海克斯強化的 +／++ 版本圖示相同，只有在已選海克斯強化欄完整時才判斷是哪一版，否則標示「階段無法判斷」。

## 本機程式（選用，舊版方式）

`ebs.py`、`companion.py` 等 Python 程式是 0.3 版以前的比對方式，0.4.0 起不再需要。若要使用，在擴充功能設定把來源改成「本機 ebs.py（備用）」，並參考 [docs/install.md](docs/install.md#選用本機程式)。

## 授權

程式碼以 [MIT License](LICENSE) 釋出。Riot Games 的遊戲資料、文字與圖示不在 MIT 授權範圍內。安裝檔內含的 OpenCV（Apache-2.0）與 Emscripten 授權見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 聲明

TFT羈絆提示（TFT Trait Hover）未經 Riot Games 認可，不代表 Riot Games 或任何正式參與製作、管理 Riot Games 作品者的觀點或意見。Riot Games 及所有相關作品皆為 Riot Games, Inc. 的商標或註冊商標。

TFT Trait Hover isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
