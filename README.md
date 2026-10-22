# 雲頂羈絆提示 本機程式（TFT Trait Hover Companion）

[English](README.en.md) · [隱私權政策 / Privacy Policy](docs/privacy.md)

Chrome 擴充功能「雲頂羈絆提示」要搭配這個本機程式使用。擴充功能把 Twitch／YouTube 播放器的畫面送到你自己電腦上的 `http://127.0.0.1:8766`，由這裡比對羈絆與海克斯圖示，只回傳時間、圖示編號和框的位置。畫面不會離開你的電腦。不顯示勝率、平均名次或推薦，也不追蹤對手。

擴充功能本身請從 Chrome 線上應用程式商店安裝（不公開項目，透過連結取得）。

## 1. 第一次安裝

需要 Python 3.9 以上。

**Mac**（終端機）：
```
python3 --version          # 需要 3.9 以上；沒有就裝 https://www.python.org/downloads/
git clone https://github.com/lamb-liver/tft-trait-hover-companion.git
cd tft-trait-hover-companion
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python companion.py fetch     # 第一次啟動前必跑：下載羈絆／海克斯圖示與目錄，幾分鐘，最後印「fetch 完成」
.venv/bin/python ebs.py --extension-id <商店 ID>
```

**Windows**（PowerShell；從 python.org 安裝 Python 時勾選「Add python.exe to PATH」）：
```
py --version
git clone https://github.com/lamb-liver/tft-trait-hover-companion.git
cd tft-trait-hover-companion
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python companion.py fetch
.venv\Scripts\python ebs.py --extension-id <商店 ID>
```

沒有 git 時，可以在本頁按「Code → Download ZIP」，解壓縮後 `cd` 進資料夾。

`--extension-id` 讓本機程式只接受商店版擴充功能連進來（ID 在 `chrome://extensions`）。也可以設環境變數 `TFT_EXTENSION_ID`，或把 ID 寫進 `data/extension_id`。

## 2. 每次看直播

1. 開終端機，到這個資料夾執行 `ebs.py`（上面最後一行），視窗開著別關。
2. 打開正在玩 TFT 的 Twitch 直播或 YouTube 影片。
3. 點工具列的「雲頂羈絆提示」，或按 Alt+Shift+Y（Mac：Option+Shift+Y），角標出現「讀」就開始。
4. 滑鼠停在左側羈絆、海克斯選擇卡或左上角已選海克斯上，就會出現繁中名稱與公開敘述。再點一次停止。

## 3. 遊戲改版後

```
git pull
.venv/bin/python companion.py fetch     # Windows：.venv\Scripts\python companion.py fetch
```
然後重開 `ebs.py`。

## 疑難排解

- 角標「?」：本機程式沒開或沒有回應，確認終端機裡 `ebs.py` 還在跑。
- 角標「!」：拿不到分頁畫面，或擴充功能和本機程式版本不合。回到直播分頁再點一次；仍不行就兩邊都更新到最新版。
- 有「讀」但沒有框：把播放器放大或全螢幕。大廳、選秀等沒有羈絆欄的畫面本來就不顯示；畫面太小或太模糊時寧可不顯示。
- 快捷鍵沒反應：到 `chrome://extensions/shortcuts` 設定一次。

## 已知限制

- 不支援手機版 TFT 的畫面。
- 名稱相同的海克斯若無法判斷輪次，會同時列出幾個候選。

## 授權

授權條款尚未決定，目前未附 LICENSE。

## 聲明

雲頂羈絆提示（TFT Trait Hover）未經 Riot Games 認可，不代表 Riot Games 或任何正式參與製作、管理 Riot Games 作品者的觀點或意見。Riot Games 及所有相關作品皆為 Riot Games, Inc. 的商標或註冊商標。
