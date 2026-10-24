# TFT Trait Hover (TFT羈絆提示)

[繁體中文](README.md) · [Install guide](docs/install.md) · [Privacy Policy](docs/privacy.md) · [Changelog](CHANGELOG.md)

While watching Teamfight Tactics on Twitch or YouTube, hover over a trait or augment icon in the player to see its Traditional Chinese name and the public in-game description.

- Since 0.4.0 it is a pure Chrome extension: **no Python or other program to install**.
- All matching runs inside your browser. Frames are never uploaded and no data is collected.
- Shows only in-game names and descriptions. No recommendations, no opponent tracking.

## Install

**Chrome Web Store**: under review. The (unlisted) store link will be added here after approval; it installs in one click and updates automatically.

**Early testing (load unpacked, desktop Chrome on Mac/Windows)**:

1. Download `tft-trait-hover-0.4.2.zip` from [Releases](https://github.com/lamb-liver/tft-trait-hover-companion/releases).
2. Unzip it into a permanent folder (don't delete or move it later).
3. Open `chrome://extensions`.
4. Turn on **Developer mode** (top right).
5. Click **Load unpacked** and select the folder that contains `manifest.json`.

See [docs/install.md](docs/install.md) for details and troubleshooting.

## Use

1. Open a Twitch stream or YouTube video of TFT.
2. Click the toolbar icon or press Alt+Shift+Y (Mac: Option+Shift+Y). The badge shows 「讀」 while reading.
3. Hover over traits on the left, augment choice cards, or picked augments at the top left. Click again to stop.

## Extras

- **Power-saving mode** (extension settings): at least 3 s between scans, pauses 20 s after the pointer leaves the player. Even without it, scanning pauses when the tab is hidden, the video is paused or the pointer has been away for a minute.
- **Report wrong result** (button at the top right of the player while reading): saves the frame and results as a file in your Downloads folder; nothing is uploaded. Attach it to an [issue](https://github.com/lamb-liver/tft-trait-hover-companion/issues) if you want to report it.
- **Tier unknown**: augment +/++ tiers share an icon; when the tier can't be determined the tooltip says so and lists every tier.

## Known limitations

- Mobile TFT layouts are not supported; mobile browsers cannot install extensions.
- Korean/Japanese stream overlays may hide some traits; the extension prefers showing nothing over guessing.
- Augment +/++ variants share the same art; the tier is only shown when the picked-augment bar is complete.

## Local program (optional, legacy)

The Python programs (`ebs.py`, `companion.py`) were the matcher before 0.4.0 and are no longer needed. See [docs/install.md](docs/install.md#optional-local-program).

## License

Code is released under the [MIT License](LICENSE). Riot Games data, text and icons are not covered. OpenCV (Apache-2.0) and Emscripten licenses bundled in the zip are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Legal

TFT Trait Hover isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
