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
| DA_18_CovenTraitAugment_LootToAP | Dark Ritual | Twitch VOD 2903227406 @ 97:30 | calibrated on known cards |
| DA_18_FaeTraitAugment | Embiggen | Twitch VOD 2907595335 @ 213:15 | calibrated on known cards |
| DA_18_ResidualMagicPlusPlus | Residual Magic ++ | Twitch VOD 2906626322 @ 244:45 | calibrated on known cards |
| DA_BlackthornTraitAugment | ItemE Extraction (read by eye: Item Extraction) | Twitch VOD 2903227406 @ 46:45 | calibrated on known cards |
| DA_ChampDelivery | Champ Delivery | Twitch VOD 2907053247 @ 89:45 | calibrated on known cards |
| DA_ChampDeliveryPlus | Champ Delivery+ | Twitch VOD 2907487096 @ 130:45 | calibrated on known cards |
| DA_ComponentQuest | Component Quest | Twitch VOD 2907487096 @ 82:15 | calibrated on known cards |
| DA_FutureFocused | Future Focused | Twitch VOD 2907854923 @ 10:00 | calibrated on known cards |
| DA_NestingAnvils | Nesting Anvils | Twitch VOD 2907487096 @ 429:45 | calibrated on known cards |
| DA_NestingAnvilsPlus | Nesting Anvils+ | Twitch VOD 2907487096 @ 231:00 | calibrated on known cards |
| DA_VerticalityII | Verticality II | Twitch VOD 2907595335 @ 105:15 | default card geometry |

DA_18_RiftbeastTraitAugment (bar crop above) was later confirmed by an OCR'd card titled "Omega Riftbeast" (Twitch VOD 2906626322 @ 8:45) showing the same glyph.

Champ Delivery and Champ Delivery+ share the same card art, as do Nesting Anvils and Nesting Anvils+. The card titles and the art from separate cards were compared by eye. Each pair uses one file (the "+" card's crop), so the two ids form a same-icon group and the tier is not guessed.

### Batch 3
| id | on-screen title | source | cut |
|---|---|---|---|
| DA_CapitalGainsII | Capital Gains II | Twitch VOD 2906615325 @ 23:45 | calibrated on known cards |
| DA_18_ElderwoodTraitAugment | Nature's Shelter | Twitch VOD 2906615325 @ 82:45 | calibrated on known cards |
| DA_18_FloraFatalisAugment | Consuming Flora | Twitch VOD 2906598662 @ 53:30 | calibrated on known cards |
| DA_18_PrimalAugment_Nidalee, DA_18_PrimalAugment_Sivir, DA_18_PrimalAugmentPlus_Nidalee, DA_18_PrimalAugmentPlus_Sivir | Beast tWithin+ | Twitch VOD 2907241009 @ 249:00 | calibrated on known cards |

Beast Within and Beast Within+ show the same art: cards titled "Beast Within" (Twitch VOD 2906626322 @ 54:00) and "Beast Within+" were compared by eye. The visible card text cannot tell the Nidalee and Sivir variants apart, so all four ids share one file and form a same-icon group (4 members).
