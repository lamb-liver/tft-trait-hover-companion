# TFT Trait Hover Companion

[繁體中文](README.md) · [Privacy Policy](docs/privacy.md)

The local companion for the TFT Trait Hover Chrome extension. The extension sends frames of the Twitch/YouTube player to `http://127.0.0.1:8766` on your own computer; this program matches trait and augment icons there and returns only a time, icon ids and box positions. Frames never leave your computer. No win rates, average placements, recommendations or opponent tracking.

Install the extension itself from the Chrome Web Store (unlisted; via link).

## 1. First-time setup

Requires Python 3.9+.

**Mac** (Terminal):
```
python3 --version
git clone https://github.com/lamb-liver/tft-trait-hover-companion.git
cd tft-trait-hover-companion
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python companion.py fetch     # required before first start: downloads trait/augment icons and catalog; a few minutes
.venv/bin/python ebs.py --extension-id <store ID>
```

**Windows** (PowerShell; tick "Add python.exe to PATH" when installing Python from python.org):
```
py --version
git clone https://github.com/lamb-liver/tft-trait-hover-companion.git
cd tft-trait-hover-companion
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python companion.py fetch
.venv\Scripts\python ebs.py --extension-id <store ID>
```

Without git, use "Code → Download ZIP" and `cd` into the extracted folder.

`--extension-id` makes the companion accept only the store extension (ID shown in `chrome://extensions`). You can also set `TFT_EXTENSION_ID` or write the ID to `data/extension_id`.

## 2. Every time you watch

1. Run `ebs.py` in this folder and keep the window open.
2. Open a TFT stream on Twitch or a TFT video on YouTube.
3. Click the toolbar icon or press Alt+Shift+Y (Mac: Option+Shift+Y); the badge shows "讀".
4. Hover trait icons, augment choice cards or the picked-augment bar.

## 3. After a game patch

Run `git pull`, then `companion.py fetch` again, and restart `ebs.py`.

## Troubleshooting

- Badge "?": the companion isn't running or not responding.
- Badge "!": the tab can't be captured, or the extension and companion versions differ — update both.
- "讀" but no boxes: enlarge the player or go fullscreen. Lobby/carousel screens show nothing; tiny or blurry players show nothing rather than guess.
- Shortcut not working: set it at `chrome://extensions/shortcuts`.

## Known limits

- Mobile TFT is not supported.
- Augments sharing one icon may list several candidates when the round can't be determined.

## License

License not chosen yet; no LICENSE file for now.

## Disclaimer

TFT Trait Hover isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
