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

### Batch 4
| id | on-screen title | source | cut |
|---|---|---|---|
| DA_18_SolarTraitAugment | 太阳的抉择 (zh-CN client; the CDragon zh_cn name for this id), read by eye | Bilibili BV1mdYj6CExx cover (author 绣汐), 273×228 thumbnail | Located with the trait-augment hex frame (Fae HUD icon, 0.76), 40 px, upscaled to 128 with INTER_CUBIC |

Checks for the zh-CN source:
- In a full frame from the same author (2-1 choice screen), the zh-CN card art for 资本利得 II matches the Twitch DA_CapitalGainsII crop at 0.948, so the CN client draws the same art.
- Reducing that Capital Gains II card to the same 37 px and upscaling it still scores 0.96 to 0.975 against the good crop at bar and card sizes, so the low-resolution cut is usable.
| DA_18_WispRebatePlus | 仙灵报恩. CDragon zh_cn has 仙灵报恩 = WispRebatePlus (StartingGold 4) and 仙灵报恩+ = PlusPlus (8). The card text reads 立刻获得4金币, which identifies this one as Plus | Bilibili BV1RW8y68EVr cover, 2560×1440, large card with name and description | 190 px card icon reduced to 128 with INTER_AREA. It matches the same augment's icon in the HUD owned-augments list of the same frame at 0.931. The 是我，宝贝! icon in that list matches DA_ItsMeBaby at 0.961 (style calibration) |
| DA_18_ResidualMagic | 残留魔力 (no "+", which is the base id) | Bilibili BV1pzYV6ZE76 cover, 1920×1080, real card crop | The card art matches the accepted DA_18_ResidualMagicPlusPlus at 0.959 (same art), so this uses the same file as ++ and forms a sameIcon group |

Rejected in batch 4:
- 创世神 (LuxII), BV1LT8w63Ezw: the named card is covered by the cover's title text (it scores only 0.66 against the clean icon in BV1MEh663EP2). The clean icon in BV1MEh663EP2 has no on-screen name, so it cannot be used either.
- 等待得值, BV1Dg8u6HEmy: the name is a cover title, not card text, and the icon has been redrawn into a round badge.
- 意外之礼, BV1v7p76PEMj: no card name, and the tier (Plus or not) cannot be proven.
| DA_18_WispRebatePlusPlus | "Wisp Rebate +" (EN). CDragon EN has Wisp Rebate+ = PlusPlus. Card in 702 frame field5/yt_cammy1440a/t857 | Same art as WispRebatePlus: that card's icon scores 0.863 against the Plus crop (the card is dimmed). Uses the same file as Plus and forms a sameIcon group | In the hud4 702 run this frame was detected as WispRebatePlus; the group fixes the tier ambiguity |
| DA_18_LunarTraitAugmentPlus | 日月同辉+ (zh-CN). The card reads 获得1个蕾欧娜、凯尔和厄斐琉斯 (Aphelios), which is the Plus description; base gives Diana | Bilibili BV1ihYA6sEdA cover, 1920×1080, large augment panel with name and description | Hex frame located by colour (290×332 px), square crop, INTER_AREA to 128. It matches the same icon in the HUD owned-augments column of the same frame at 0.963 (Solar 0.54, Fae 0.52). Base art not proven, so the base id stays a placeholder |
