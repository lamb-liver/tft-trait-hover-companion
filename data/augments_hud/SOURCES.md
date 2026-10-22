# augments_hud sources

These icons were cut from real game frames. Each one replaces CDragon's placeholder icon (hexcore/missing-t*), or an icon that the HUD draws differently. Raw frames are not committed.

How each icon was identified and cut:
- The augment was identified only by the card title on screen, either OCR'd (rapidocr, exact name match) or read by eye. Never by shape.
- The icon is the 144 px card square at 1080p, cut at y=348 and x=477, 886 or 1296.
- Where the same frame had other cards with known CDragon icons (match ≥ 0.85), the cut position was calibrated against them.
- The crop is resized to 128 px with INTER_AREA.

| id | on-screen title | source | cut |
|---|---|---|---|
| DA_18_RiftbeastTraitAugment | (selected bar, user crop) | user screenshot 2026-10-22 | calibrated on DA_SmallGrabBag (0.934) |
| DA_JeweledLotus_I | (selected bar, user crop) | user screenshot 2026-10-22 | CDragon raw jeweled-lotus scan 0.86 |
| DA_18_CovenTraitAugment | Coven Acolyte | Twitch VOD 2907857887 @ 65:00 | calibrated on known cards |
| DA_18_FOURcing | FOURcing | Twitch VOD 2907857887 @ 73:30 | calibrated on known cards |
| DA_18_RivalsAugment | Unrivaled | Twitch VOD 2907857887 @ 114:30 | calibrated on known cards |
| DA_18_SprykinAugment | Small Furry Friend | Twitch VOD 2907050837 @ 43:45 | default card geometry |
| DA_BonusGift | Bonus Gifts | Twitch VOD 2907857887 @ 65:15 | calibrated on known cards |
| DA_CapitalGainsI | Capital Gains I (OCR "Capital Gains", read by eye) | Twitch VOD 2907857887 @ 106:15 | calibrated on known cards |
| DA_ItsMeBaby | It's Me, Baby | Twitch VOD 2907857887 @ 9:45 | default card geometry |
| DA_LoadedDice | Loaded Dice | Twitch VOD 2907857887 @ 106:15 | calibrated on known cards |
| DA_QuickStreaks | Quick Streaks | Twitch VOD 2906297245 @ 52:00 | calibrated on known cards |
| DA_TraitLadder | Trait Ladder | YouTube kCcMM-kD5o4 @ ~0:20 | calibrated on known cards |
| DA_VerticalityI | Verticality I (OCR "Verticality !", read by eye) | data/real field7/xsweet_poison/s-172925.png | calibrated on known cards |
| DA_VerticalityIII | Verticality III | YouTube kCcMM-kD5o4 @ ~9:18 | calibrated on known cards |
