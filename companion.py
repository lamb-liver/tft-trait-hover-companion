#!/usr/bin/env python3
"""Streamer-side companion.

Reads the left side of a frame, matches trait icons, and posts ids plus
boxes. Descriptions stay in viewer/catalog.json, built from CommunityDragon
and Data Dragon.
"""

import argparse
import concurrent.futures
import hashlib
import json
import threading
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

# The batched shortlist runs inside our own thread pools; a second layer of BLAS threads
# oversubscribes the cores and is slower (0.65 s vs 0.40 s per frame on 8 cores).
for _blas in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_blas, "1")

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CATALOG = ROOT / "viewer" / "catalog.json"
UA = {"User-Agent": "tft-trait-hover"}
TOKEN = re.compile(r"@([A-Za-z0-9_]+)(?:\*([0-9.]+))?@")
LIVE_TOKEN = re.compile(r"@[A-Za-z_][^@]*[.:][^@]*@")
ROW = re.compile(r"<row>(.*?)</row>", re.I | re.S)
ICON_TAG = re.compile(r"%i:([^%]+)%")
TAG = re.compile(r"<[^>]+>")
CJK = re.compile(r"[\u4e00-\u9fff]")
ONLY_COUNT = re.compile(r"^\(\d+\)$")
BARE_PERCENT = re.compile(r"(?<!\d)%")
LIVE_NOW = re.compile(r"[（(]目前[^）)]*[）)]")
FROZEN_NOW = re.compile(r"^目前：\d*$")
# A short empty label ("英雄：", "目前環境：") or a baked zero
# ("種子：0 / 5", "擊殺數：0"). A longer clause ending in ： introduces the
# rows under it and stays (絕命花華「…收割目標，獲得：」).
LIVE_LINE = re.compile(
    r"^(?:[^。！？\d：]{1,16}：\s*|[^。！？]{1,30}：\s*0(?:\s*/\s*\d+)?\s*)$"
)
LIVE_LABEL = re.compile(r"^[^。！？\d]{1,16}：\s*(?:金錢|生命)?\s*$")
LIVE_RATIO = re.compile(r"^[^。！？]{0,24}：\s*/\s*\d+\s*$")
LIVE_CAP = re.compile(r"上限：0/(\d+)")
LIVE_MAX = re.compile(r"最多/(\d+)")
LIVE_ZEROS = re.compile(r"(?<=。)\s*0(?:\s+0)+")
BODY = re.compile(r"^\(\d+\)\s*")
# Bump this when a published sentence changes, so a stale file is refetched.
CATALOG_VERSION = 7
STAT_LABEL = {
    "scaleAD": "物攻",
    "scaleAP": "魔攻",
    "scaleAS": "攻速",
    "scaleHealth": "生命",
    "scaleArmor": "護甲",
    "scaleMR": "魔抗",
    "scaleDR": "續戰力",
    "scaleManaRegen": "魔力回復",
}
ROI_FRACTION = 0.20
# 24px locks onto HUD text (平均名次 scored 0.85 on a stream). Active badges
# draw the glyph dark-on-gold, which is the alpha inverted; inactive stay light.
SCALES = (32, 36, 40, 48, 64, 80)
AUGMENT_SCALES = (48, 64, 80, 96)
THRESHOLD = 0.72
# ponytail: one peak per trait. On the 2-7 stream, real badges cleared the next
# peak by >=0.24; the scoreboard lookalike cleared it by 0.16. Two real copies
# at the same scale need a multi-peak pass.
PEAK_GAP = 0.20
# A neighboring gold hex shares the frame, so a real badge can clear the next
# peak by only 0.16 (絕命花華 0.889 at the icon, second peak on 重裝戰士).
# Lookalikes at that gap scored <= 0.81. Upgrade path: multi-peak per trait.
STRONG = 0.86
STRONG_GAP = 0.14
# Search at 1/3. Sprykin at that size scored 0.854 with a gap of 0.185, just
# outside the gate, and passed again at 1/2 (0.881, gap 0.201). Scoreboard
# lookalikes stayed under a 0.14 gap, so they are not rechecked.
SEARCH_STEP = 3
RECHECK_STEP = 2
NEAR_SCORE = 0.80
# 1920×1080 augment-select glyphs. x = name-band center (TFT-Copilot
# vision/hud/regions.json: 550, 958, 1369) minus half of 96. y is the glyph
# top measured on examples/augments.png, whose gold sits in y 362–463.
AUGMENT_SLOT = (
    ("TFT9_Augment_OneTwosThree", 502, 364),
    ("DA_CelestialBlessingI", 910, 364),
    ("TFT10_Augment_FullyAdapted", 1321, 364),
)
AUGMENT_SIDE = 96
# A row that is only a number. The label is the stat the token already names.
ROW_LABEL = {
    "ADAPGain": "物攻或魔攻",
    "DefenderDefenseGain": "雙防",
}
# cdragon stores these as null. SeeMeta and Blitz state the same number (2026-10-16).
# ponytail: delete a key when cdragon ships a real value.
PUBLIC_NULL = {
    "TFT_Augment_DeadlierCaps": {"AP": 1},
    "TFT_Augment_TragicalBlade": {"AD": 0.01},
}
# The four blessings are a live pick, not a sentence in cdragon. MetaTFT and
# Blitz zh-TW agree. ponytail: delete when cdragon includes the blurbs.
PUBLIC_LINES = {
    "DA_Primal18": [
        "在四大野性祝福中選擇一項。",
        "野性傷害將處決生命低於12%的敵軍。",
        "野性英雄每參與擊殺15次，獲得1個組件。上限為4。",
        "經過6秒後，野性英雄獲得35%攻速，我方隊伍獲得15%攻速。",
        "我方隊伍每4秒回復最大生命的4%。",
        "(2) 選擇一項祝福。",
        "(4) 選擇第二項祝福。",
    ],
}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def fnv1a(text):
    value = 0x811C9DC5
    for byte in text.lower().encode():
        value ^= byte
        value = (value * 0x01000193) & 0xFFFFFFFF
    return f"{value:08x}"


def lookup(variables, name):
    for key, value in variables.items():
        if key.lower() == name.lower():
            return value
    hashed = fnv1a(name)
    for key, value in variables.items():
        if key.strip("{}").lower() == hashed:
            return value
    return None


def fmt(number):
    number = float(number)
    if abs(number - round(number)) < 0.051:
        return str(int(round(number)))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def fill(text, effect, effects):
    def repl(match):
        name, mul = match.group(1), match.group(2)
        if name == "MinUnits":
            return str(effect.get("minUnits", ""))
        value = lookup(effect.get("variables") or {}, name)
        if value is None:
            for other in effects:
                value = lookup(other.get("variables") or {}, name)
                if value is not None:
                    break
        if value is None:
            return match.group(0)
        if mul:
            value = float(value) * float(mul)
        return fmt(value)

    return TOKEN.sub(repl, text)


def stat_sub(match):
    label = STAT_LABEL.get(match.group(1))
    if label is None:
        return match.group(0)
    return " " + label


def lines_of(text):
    text = ICON_TAG.sub(stat_sub, unescape(text))
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = TAG.sub("", text)
    out = []
    for line in text.split("\n"):
        line = re.sub(r" {2,}", " ", line).strip()
        line = re.sub(r"或\s*$", "", line).strip()
        line = LIVE_CAP.sub(r"上限為\1", line)
        line = LIVE_MAX.sub(r"最多\1", line)
        line = LIVE_ZEROS.sub("", line).strip()
        if line.endswith("，"):
            line = line[:-1] + "。"
        if (
            not line
            or ONLY_COUNT.fullmatch(line)
            or FROZEN_NOW.fullmatch(line)
            or LIVE_LINE.fullmatch(line)
            or LIVE_LABEL.fullmatch(line)
            or LIVE_RATIO.fullmatch(line)
            or live_blank(line)
        ):
            continue
        # An unknown %i: tag stays in the line. fetch refuses to publish it.
        if "%i:" not in line and CJK.search(line) is None:
            continue
        out.append(line)
    return join_parens(out)


def numeric_effects(item):
    effects = {
        key: value
        for key, value in (item.get("effects") or {}).items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }
    for key, value in PUBLIC_NULL.get(item.get("apiName"), {}).items():
        effects.setdefault(key, value)
    return effects


def resolved_sentences(line):
    """Drop a sentence that still has an unfilled token. Keep the sentences around it."""
    if "@" not in line and not BARE_PERCENT.search(line):
        return line
    kept = [
        part
        for part in re.split(r"(?<=。)", line)
        if part and "@" not in part and "%i:" not in part and not BARE_PERCENT.search(part)
    ]
    return "".join(kept).strip()


def describe_augment(item):
    """Public text only. Live counters such as TFTUnitProperty stay out of the card."""
    variables = numeric_effects(item)
    text = LIVE_NOW.sub("", LIVE_TOKEN.sub("", item.get("desc") or ""))
    text = fill(text, {"minUnits": "", "variables": variables}, [{"variables": variables}])
    kept = []
    for line in lines_of(text):
        if "%i:" in line:
            kept.append(line)
            continue
        line = resolved_sentences(line)
        if line:
            kept.append(line)
    return dedupe(kept)


def unmapped_lines(cards):
    return [
        f"{card['name']}: {line}"
        for card in cards.values()
        for line in card["lines"]
        if "%i:" in line
    ]


def guard_mapped(traits, augments):
    bad = unmapped_lines(traits) + unmapped_lines(augments)
    if bad:
        preview = "\n".join(bad[:8])
        raise SystemExit(f"unmapped stat icon, catalog not updated\n{preview}")


def describe(trait):
    effects = trait.get("effects") or [{"minUnits": "", "variables": {}}]
    rows = ROW.findall(trait["desc"])
    preamble = ROW.sub("", trait["desc"])
    lines = lines_of(fill(preamble, effects[0], effects))
    for index, row in enumerate(rows):
        effect = effects[index] if index < len(effects) else effects[-1]
        filled = fill(row, effect, effects)
        label = next((ROW_LABEL[name] for name, _mul in TOKEN.findall(row) if name in ROW_LABEL), "")
        if label and label not in filled:
            filled = re.sub(r"或\s*$", "", filled).rstrip() + " " + label
        lines.extend(lines_of(filled))
    lines = [team_or_self(line, trait.get("name") or "") for line in join_parens(lines)]
    return dedupe(lines)


def live_blank(line):
    """A label whose value was a live token and is now only punctuation."""
    if "：" not in line or "。" in line:
        return False
    label, _, value = line.partition("：")
    if len(label) > 16:
        return False
    return CJK.search(value) is None and re.search(r"\d", value) is None


def dedupe(lines):
    out, seen = [], set()
    for line in lines:
        key = BODY.sub("", line)
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out


def join_parens(lines):
    """A line break inside one parenthetical is still one sentence."""
    out = []
    for line in lines:
        if out and out[-1].count("(") + out[-1].count("（") > out[-1].count(")") + out[-1].count("）"):
            sep = "" if out[-1][-1] in "，、；：" or line[:1] in "，、；：)" else "，"
            out[-1] = out[-1] + sep + line
            continue
        out.append(line)
    return out


def team_or_self(line, trait_name):
    """'4% 續戰力或20% 續戰力' is the team bonus, then the trait's own bonus."""
    found = re.fullmatch(r"(\(\d+\))\s*(\d+%)\s*([^\s或]+)或\s*(\d+%)\s*\3", line.strip())
    if not found or not trait_name:
        return line
    count, left, stat, right = found.groups()
    if float(left[:-1]) >= float(right[:-1]):
        return line
    return f"{count} 隊伍{left} {stat}，{trait_name}{right} {stat}"


def public_name(item):
    variables = numeric_effects(item)
    text = fill(item.get("name") or "", {"minUnits": "", "variables": variables}, [{"variables": variables}])
    text = TAG.sub("", unescape(text))
    text = re.sub(r"@[^@]*@", "", text)
    return re.sub(r" {2,}", " ", text).strip()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def read_catalog():
    try:
        return json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def catalog_is_current(payload, live=None):
    if not isinstance(payload, dict):
        return False
    traits = payload.get("traits")
    augments = payload.get("augments")
    if payload.get("version") != CATALOG_VERSION or not isinstance(traits, dict) or not traits:
        return False
    if not isinstance(augments, dict) or not augments:
        return False
    if live is not None and payload.get("patch") != live:
        return False
    return True


def catalog_decision(payload, live):
    """keep the file, fetch a new one, or fail because the file is stale and we are offline."""
    if live is None:
        return "keep" if catalog_is_current(payload) else "fail"
    return "keep" if catalog_is_current(payload, live) else "fetch"


def live_patch():
    try:
        return get_json("https://ddragon.leagueoflegends.com/api/versions.json")[0]
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return None


def traits_of(payload):
    if isinstance(payload, dict) and isinstance(payload.get("traits"), dict):
        return payload["traits"]
    return payload if isinstance(payload, dict) else {}


def current_set(payload):
    best = None
    for entry in payload["setData"]:
        number = entry.get("number")
        if entry.get("mutator") == f"TFTSet{number}" and (
            best is None or number > best["number"]
        ):
            best = entry
    return best


def save_url(url, dest):
    if dest.is_file() and dest.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as response:
            dest.write_bytes(response.read())
        return True
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 404):
            return False
        raise


def fetch():
    DATA.mkdir(parents=True, exist_ok=True)
    version = get_json("https://ddragon.leagueoflegends.com/api/versions.json")[0]
    dragon = get_json(
        f"https://ddragon.leagueoflegends.com/cdn/{version}/data/zh_TW/tft-trait.json"
    )["data"]
    augment_dragon = get_json(
        f"https://ddragon.leagueoflegends.com/cdn/{version}/data/zh_TW/tft-augments.json"
    )["data"]
    cdragon = get_json("https://raw.communitydragon.org/latest/cdragon/tft/zh_tw.json")
    chosen = current_set(cdragon)
    units = {}
    for champion in chosen["champions"]:
        cost = champion.get("cost") or 0
        if cost < 1:
            continue
        for trait_name in champion.get("traits") or []:
            units.setdefault(trait_name, []).append((cost, champion["name"]))

    catalog = {}
    icons = DATA / "icons"
    icons.mkdir(exist_ok=True)
    missing = []
    for trait in chosen["traits"]:
        card = dragon.get(trait["apiName"])
        if not card:
            missing.append(trait["apiName"])
            continue
        filename = card["image"]["full"]
        dest = icons / f"{trait['apiName']}.png"
        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/tft-trait/{filename}"
        if not save_url(url, dest):
            missing.append(trait["apiName"])
            continue
        members = units.get(trait["name"], [])
        members.sort()
        catalog[trait["apiName"]] = {
            "name": trait["name"],
            "lines": PUBLIC_LINES.get(trait["apiName"], describe(trait)),
            "units": "、".join(name for _cost, name in members),
        }
    by_api = {item["apiName"]: item for item in cdragon["items"] if item.get("isAugment")}
    augments = {}
    for api in chosen["augments"]:
        item = by_api.get(api)
        if not item:
            missing.append(api)
            continue
        augments[api] = {"name": public_name(item), "lines": describe_augment(item)}
    guard_mapped(catalog, augments)
    icons = DATA / "augments"
    icons.mkdir(exist_ok=True)
    no_icon = []
    for index, api in enumerate(augments, start=1):
        card = augment_dragon.get(api)
        if not card:
            no_icon.append(api)
            continue
        dest = icons / f"{api}.png"
        filename = card["image"]["full"]
        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/tft-augment/{filename}"
        if not save_url(url, dest):
            no_icon.append(api)
        if index % 100 == 0:
            print(f"augment icons {index}/{len(augments)}", flush=True)
    write_json(
        CATALOG,
        {
            "version": CATALOG_VERSION,
            "patch": version,
            "set": chosen["number"],
            "traits": catalog,
            "augments": augments,
        },
    )
    write_json(DATA / "set.json", {"set": chosen["number"], "patch": version, "catalog": CATALOG_VERSION})
    import ebs

    ebs.publish_traits()
    print(
        f"set {chosen['number']}  {len(catalog)} traits  {len(augments)} augments"
        f"  patch {version}  catalog v{CATALOG_VERSION}"
    )
    if missing:
        print("no trait icon:", ", ".join(missing))
    if no_icon:
        print(f"no augment icon: {len(no_icon)}")
    return catalog


def ensure_catalog():
    payload = read_catalog()
    decision = catalog_decision(payload, live_patch())
    if decision == "keep":
        return payload["traits"]
    if decision == "fail":
        raise SystemExit("catalog is stale and Data Dragon is unreachable")
    return fetch()


# The in-game HUD can draw a different glyph than the CDragon icon (2026-10-21:
# Invoker is a goblet in CDragon, a drop under arcs on the HUD; it never matched).
# data/icons_hud holds masks traced from a real badge and wins over data/icons.
# fetch does not touch it.
HUD_ICONS = DATA / "icons_hud"


def load_alpha(trait_id):
    path = HUD_ICONS / f"{trait_id}.png"
    if not path.is_file():
        path = DATA / "icons" / f"{trait_id}.png"
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None or image.ndim != 3 or image.shape[2] < 4:
        return None
    alpha = image[:, :, 3]
    if int(alpha.max()) - int(alpha.min()) < 8:
        return None
    return alpha


def load_templates():
    catalog = traits_of(json.loads(CATALOG.read_text(encoding="utf-8")))
    templates = []
    for trait_id in catalog:
        alpha = load_alpha(trait_id)
        if alpha is not None:
            templates.append((trait_id, alpha))
    return templates


def paint(frame, alpha, x, y, side):
    mask = cv2.resize(alpha, (side, side), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    region = frame[y : y + side, x : x + side].astype(np.float32)
    painted = region * (1 - mask[..., None]) + 235 * mask[..., None]
    frame[y : y + side, x : x + side] = painted.astype(np.uint8)


def best_peak(result, side):
    _min, score, _min_at, where = cv2.minMaxLoc(result)
    x, y = where
    masked = result.copy()
    masked[max(0, y - side) : y + side, max(0, x - side) : x + side] = -1
    _min2, second, _min_at2, _where2 = cv2.minMaxLoc(masked)
    return float(score), float(second), x, y


# ponytail: resized needles stay for the process. Restart after fetch replaces icons.
_SCALED = {}


def _down(gray, step):
    if step <= 1:
        return gray
    height, width = gray.shape[:2]
    return cv2.resize(
        gray,
        (max(1, width // step), max(1, height // step)),
        interpolation=cv2.INTER_AREA,
    )


def _needles(trait_id, alpha, step):
    key = (trait_id, step)
    cached = _SCALED.get(key)
    if cached is not None:
        return cached
    made = []
    for side in SCALES:
        small = side // step
        if small < 8:
            continue
        image = cv2.resize(alpha, (small, small), interpolation=cv2.INTER_AREA)
        made.append((side, small, image, 255 - image))
    _SCALED[key] = made
    return made


def _glyph_mask(image, needle, key):
    """The glyph plus a thin rim. Corners of the square hold the badge's hex frame,
    which every trait shares; on blurry 720p it gave 0.7-0.8 runner-up peaks on
    other rows, so true badges at 0.83-0.88 failed the gap (field test 2, mili)."""
    # Keyed by trait, step and size, not id(image): two threads can build the same
    # needle at once, and a freed image's id can come back on a different size.
    got = _SCALED.get(key)
    if got is None:
        grown = cv2.dilate(image, np.ones((3, 3), np.uint8), iterations=max(1, needle // 10))
        got = (grown > 20).astype(np.uint8) * 255
        _SCALED[key] = got
    return got


def _search(small, trait_id, alpha, step, masked=False):
    best = None
    for side, needle, image, inverted in _needles(trait_id, alpha, step):
        if needle >= small.shape[0] or needle >= small.shape[1]:
            continue
        mask = _glyph_mask(image, needle, ("mask", trait_id, step, side)) if masked else None
        # TM_CCOEFF_NORMED subtracts the template mean, so the inverted glyph
        # (255 - image) scores exactly the negative of the glyph: one call, two maps.
        plain = cv2.matchTemplate(small, image, cv2.TM_CCOEFF_NORMED, mask=mask)
        for result in (plain, -plain):
            if masked:
                result = np.nan_to_num(result, nan=-1.0, posinf=-1.0, neginf=-1.0)
            score, second, x, y = best_peak(result, needle)
            if best is None or score > best[0]:
                best = (score, second, x * step, y * step, side, side)
    return best


def _accepts(score, second):
    gap = score - second
    return score >= THRESHOLD and (gap >= PEAK_GAP or (score >= STRONG and gap >= STRONG_GAP))


# Trait badges sit in one column. Field test 2026-10-21 (10 channels): the HUD's
# unit/item columns left of it (x 12-32 at 1920) held a leaf item that scored as
# Riftbeast on 13 frames. The column moves with layout (x 72 or 124), so take the
# median of the hits and drop ones off it. Geometry, not a second score gate.
COLUMN_SLACK = 20 / 1080


LIST_X = (40 / 1080, 160 / 1080)
LIST_Y = (0.2, 0.8)


def _in_trait_list(hit, aspect):
    x = hit["x"] * aspect
    return LIST_X[0] <= x <= LIST_X[1] and LIST_Y[0] <= hit["y"] <= LIST_Y[1]


def one_column(hits, aspect=16 / 9):
    """Keep trait hits on the column most of them share.

    Fewer than 3 hits give no column to agree on. Then keep only hits where the
    HUD's trait list sits: across 140 field frames (20 channels) every real
    column was at x 68-125 (1080-high units), y 0.25-0.70, and all four 1-2 hit
    frames were false (Dota UI, a TFT video inside a browser, a screen corner)."""
    if len(hits) < 3:
        return [h for h in hits if _in_trait_list(h, aspect)]
    xs = sorted(h["x"] for h in hits)
    mid = xs[len(xs) // 2]
    slack = COLUMN_SLACK / aspect
    return [h for h in hits if abs(h["x"] - mid) <= slack]


# Sequence mode (ebs /frame): frames between full left-20% searches, and how far
# the left-20% thumbnail may drift from the last full search's (mean abs, 0-255).
TRACK_FRAMES = 8
TRACK_DIFF = 6.0
TRACK_NEAR = 0.60


def _left_thumb(frame):
    height, width = frame.shape[:2]
    roi = cv2.cvtColor(frame[:, : max(1, int(width * ROI_FRACTION))], cv2.COLOR_BGR2GRAY)
    return cv2.resize(roi, (32, 180), interpolation=cv2.INTER_AREA).astype(np.int16)


def match(frame, templates, track=None):
    """Trait badges on one frame. track (a dict kept across frames of one stream)
    lets a frame like the last one skip most of the left-20% search: only the
    traits the last full search found are scored there. The result is used only
    when it names the same traits; anything else runs the full search."""
    if track is None:
        return _match(frame, templates)
    size = frame.shape[:2]
    thumb = _left_thumb(frame)
    if (
        track.get("size") == size
        and track.get("left", 0) > 0
        and float(np.abs(thumb - track["thumb"]).mean()) <= TRACK_DIFF
    ):
        known = [(t, a) for t, a in templates if t in track["ids"] or t in track["near"]]
        hits = _match(frame, templates, known)
        if hits is not None and {h["id"] for h in hits} == track["ids"]:
            track["left"] -= 1
            return hits
    scores = {}
    hits = _match(frame, templates, scores=scores)
    track.clear()
    track.update(
        size=size,
        thumb=thumb,
        ids={h["id"] for h in hits},
        # Traits that came close on the full search stay in the left-20% pass:
        # a badge at the gap's edge (robinsongz Hunter) shows on single frames.
        near={t for t, v in scores.items() if v >= TRACK_NEAR},
        left=TRACK_FRAMES if len(hits) >= 3 else 0,
    )
    return hits


def _match(frame, templates, known=None, scores=None):
    """Left 20%, then again on the badge column only.

    Each trait keeps its single best peak and needs a gap to the runner-up. On
    real HUDs the item column left of the badges holds lookalikes (a leaf item
    scored as Riftbeast), so the true badge lost the peak or the gap and the
    trait stayed silent even at 0.93. Field test 2026-10-21: once 3+ hits agree
    on a column, search again inside that band so items no longer compete.
    Same 0.72 gate and gap rules. known: score only these traits in the left
    20% (sequence mode); None if that finds no column."""
    height, width = frame.shape[:2]
    first = _match_band(frame, templates if known is None else known, 0, max(1, int(width * ROI_FRACTION)), scores=scores)
    column = one_column(first, width / height)
    if len(column) < 3:
        return column if known is None else None
    xs = sorted(h["x"] * width for h in column)
    side = max(h["w"] * width for h in column)
    mid = xs[len(xs) // 2]
    pad = COLUMN_SLACK * height + side
    x0 = max(0, int(mid - pad))
    x1 = min(width, int(mid + side + pad))
    # The band is ~1/17 of the left 20%, so search it at 1/2 straight away: at 1/3
    # small bronze badges (48 px) fell under NEAR_SCORE and never got the recheck,
    # though they score 0.86-0.92 at full size (field test 2026-10-21).
    started = _masked_start(frame, templates, x0, x1, {h["id"] for h in column})
    band = one_column(_match_band(frame, templates, x0, x1, RECHECK_STEP), width / height)
    # Then hits found only at 1/3 in the band, then first-pass column hits: each
    # pass can pass a gap rule another missed. The finer pass wins a shared spot.
    extra = (
        one_column(_match_band(frame, templates, x0, x1), width / height)
        + column
        + _masked_pass(frame, templates, x0, x1, {h["id"] for h in band} | {h["id"] for h in column}, started)
    )
    for hit in extra:
        ids = {h["id"] for h in band}
        if hit["id"] in ids or any(abs(hit["y"] - b["y"]) < b["h"] / 2 for b in band):
            continue
        band.append(hit)
    band.sort(key=lambda h: h["y"])
    return band + _empty_slots(frame, templates, band)


EDGE_SLOTS = True
SLOT_LOG = None  # set to a list to record every slot's top two (measurement only)


# Lead over the next trait for a slot hit. The slot is already known to hold a
# badge, so only the id is in question; 0.20 (PEAK_GAP) dropped fuutime
# Juggernaut (0.838 vs 0.664). Sweep on 140 field frames (2026-10-21): every
# slot >= 0.72 with lead 0.10-0.20 was right, nothing else in that range.
SLOT_GAP = 0.10


def _slot_accepts(score, second):
    return score >= THRESHOLD and score - second >= SLOT_GAP


def _empty_slots(frame, templates, band):
    """Rows inside the badge list with no hit: the HUD stacks badges at a fixed
    pitch, so a gap between two found badges is a badge. Match the missing traits
    there with the glyph mask and take the best only if it clears 0.72 and beats
    the next trait by PEAK_GAP, on a fill that reads as a badge (badge_tier).
    Field 2026-10-21: grey Primal, Ravager/劫掠者 (Slayer), a captioned
    Executioner, Rapidfire; 7 hits on 140 frames, every one checked by eye."""
    if len(band) < 3:
        return []
    height, width = frame.shape[:2]
    ys = sorted(h["y"] for h in band)
    pitch = float(np.median(np.diff(ys)))
    if pitch <= 0:
        return []
    have = {h["id"] for h in band}
    x = float(np.median([h["x"] for h in band]))
    w = float(np.median([h["w"] for h in band]))
    h = float(np.median([b["h"] for b in band]))
    side = int(round(h * height))
    found = []
    rows = int(round((ys[-1] - ys[0]) / pitch))
    # Also one row above the first and below the last badge. Off the list the
    # fill is HUD background, and the 0.72 / PEAK_GAP rule still has to pass.
    for i in ([-1] if EDGE_SLOTS else []) + list(range(1, rows)) + ([rows + 1] if EDGE_SLOTS else []):
        y = ys[0] + i * pitch
        if min(abs(y - other) for other in ys) < pitch / 2:
            continue
        slot = {"x": x, "y": y, "w": w, "h": h}
        if badge_tier(frame, slot) is None:
            continue
        cx, cy, reach = int((x + w / 2) * width), int((y + h / 2) * height), int(side * 0.9)
        crop = cv2.cvtColor(frame[max(0, cy - reach) : cy + reach, max(0, cx - reach) : cx + reach], cv2.COLOR_BGR2GRAY)
        scores = [(_slot_best(crop, trait_id, alpha, side), trait_id) for trait_id, alpha in templates if trait_id not in have]
        scores.sort(key=lambda item: -item[0][0])
        if len(scores) < 2:
            continue
        (score, px, py, size), trait_id = scores[0]
        if SLOT_LOG is not None:
            SLOT_LOG.append((y, trait_id, score, scores[1][1], scores[1][0][0]))
        if not _slot_accepts(score, scores[1][0][0]):
            continue
        have.add(trait_id)
        found.append({
            "id": trait_id,
            "x": (max(0, cx - reach) + px) / width,
            "y": (max(0, cy - reach) + py) / height,
            "w": size / width,
            "h": size / height,
            "score": round(score, 3),
        })
    return found


def badge_tier(frame, hit):
    """One tier per badge from the hex fill: a ring just outside the glyph box.

    Medians on 867 field badges (2026-10-21, 21 channels) form tight clusters in
    HSV: inactive V 15-25; silver H 90-94 S 31-44 V 159-166; bronze H 9-14
    S 90-130 V 61-132; gold H 22-24 S 126-147; unique (1/1, orange) H 12-14
    S 155-172 V 223-236. Prismatic never showed up, so its rule is a guess
    (pink/violet fill) and anything else gives None: no label beats a wrong one.
    The rules are disjoint, so a slot gets exactly one tier. Internal only: never
    sent in /frame or shown; today it changes no match result (140 field frames)."""
    height, width = frame.shape[:2]
    w, h = hit["w"] * width, hit["h"] * height
    cx, cy = hit["x"] * width + w / 2, hit["y"] * height + h / 2
    reach = 0.75 * h
    x0, y0 = max(0, int(cx - reach)), max(0, int(cy - reach))
    crop = frame[y0 : int(cy + reach), x0 : int(cx + reach)]
    if crop.size == 0:
        return None
    yy, xx = np.mgrid[y0 : y0 + crop.shape[0], x0 : x0 + crop.shape[1]]
    ring = np.hypot(xx - cx, yy - cy)
    ring = (ring > 0.5 * h) & (ring < 0.68 * h)
    if not ring.any():
        return None
    hue, sat, val = np.median(cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)[ring], axis=0)
    if val < 40:
        return "inactive"
    if sat < 80:
        return "silver" if val >= 100 else None
    if 18 <= hue <= 35:
        return "gold"
    if hue < 18:
        return "unique" if sat >= 150 and val >= 200 else "bronze"
    if 135 <= hue <= 175 and val >= 100:
        return "prismatic"
    return None


def one_per_slot(hits):
    """Each trait id once and each badge slot once: the higher score wins."""
    kept = []
    for hit in sorted(hits, key=lambda h: -h.get("score", 0)):
        if any(k["id"] == hit["id"] or (abs(k["y"] - hit["y"]) < k["h"] / 2 and abs(k["x"] - hit["x"]) < k["w"] / 2) for k in kept):
            continue
        kept.append(hit)
    kept.sort(key=lambda h: h["y"])
    return kept


# The HUD trait list hangs from the top: on 219 field frames (37 channels) the
# first badge sat at y 0.25-0.30. A column starting below 0.35 was an emblem
# list in an item tooltip (field 3, mb_zeref: 5 false traits), at x 184 px
# (1080-high units), right of the HUD column zone LIST_X (40-160).
# Field 5 (held out): real lists also start lower when a webcam covers the top
# rows (whoscxta 0.43), the shop or an augment pick is open (miaselenas 0.50,
# cammy 0.35-0.45) or the game is scaled down (kiyoit 0.38); all of them sat at
# x 71-131. So a low list is kept when its column is in the HUD zone.
LIST_TOP_MAX = 0.35
# Final column checks. The HUD draws every badge at one x, so the offset from
# the column median is matcher jitter only. Measured on output boxes: real
# badges <= 3.5 px (1080-high units) on 393 frames (4 batches, each batch's max
# 3.0-3.5), and <= 4.0 px on the held-out field 5 (154 frames). False ones:
# stream overlays 14-18 px (field 4: QR code, "NOW PLAYING" banner, character
# art) and a stat icon in an item tooltip 7.0 px (field 5, sunhide: Eclipse on
# "Magic Resist"). 5.5 px leaves 1.5 px either side; thin, see ADR.
# The list shows at most 10 badges before its "+N" chip: on a QR code below the
# chip a Solar sat at row 10.9 (single streamer; real lists end by row 8.1).
TIGHT_COLUMN = 5.5 / 1080
MAX_ROW = 10.5


def tight_column(hits, aspect=16 / 9):
    if len(hits) < 3:
        return hits
    mid = float(np.median([h["x"] for h in hits]))
    kept = [h for h in hits if abs(h["x"] - mid) * aspect <= TIGHT_COLUMN]
    if len(kept) < 3:
        return kept
    ys = sorted(h["y"] for h in kept)
    pitch = float(np.median(np.diff(ys)))
    if pitch <= 0:
        return kept
    return [h for h in kept if (h["y"] - ys[0]) / pitch <= MAX_ROW]


def list_from_top(hits, aspect=16 / 9):
    """Keep the list only where the HUD draws it. The item column sits left of the
    trait column (x 12-32 px, 1080-high units), so a column left of LIST_X[0] is
    items, whatever its length (field 7, snoodyboo: three item icons in a column
    read as Sprykin/Vanguard/Juggernaut). Real columns: x >= 52 px on 687 frames.
    A list starting below LIST_TOP_MAX must also sit inside LIST_X."""
    if not hits:
        return hits
    x = float(np.median([h["x"] for h in hits])) * aspect
    if x < LIST_X[0]:
        return []
    if min(h["y"] for h in hits) <= LIST_TOP_MAX:
        return hits
    return hits if x <= LIST_X[1] else []


def _slot_sizes(side):
    # One size is not enough: the Hunter badge only won at side +/- 4.
    return (side - 4, side, side + 4)


_VERIFY_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=7)


def _slot_needle(trait_id, alpha, size):
    key = ("slotneedle", trait_id, size)
    got = _SCALED.get(key)
    if got is None:
        image = cv2.resize(alpha, (size, size), interpolation=cv2.INTER_AREA)
        got = (image, 255 - image, _glyph_mask(image, size, ("slot", trait_id, size)))
        _SCALED[key] = got
    return got


def _slot_best(crop, trait_id, alpha, side):
    """Best glyph-masked score of one trait in a badge crop: (score, x, y, size).
    Sizes side-4, side, side+4, plain then inverted; the first strict maximum wins."""
    best = (-1.0, 0, 0, side)
    for size in _slot_sizes(side):
        if size < 8 or size >= min(crop.shape[:2]):
            continue
        image, _inverted, mask = _slot_needle(trait_id, alpha, size)
        # The inverted glyph scores the exact negative of the glyph (see _search):
        # one masked call, two maps. Non-finite cells read -1 in both maps.
        raw = cv2.matchTemplate(crop, image, cv2.TM_CCOEFF_NORMED, mask=mask)
        finite = np.isfinite(raw)
        for result in (np.where(finite, raw, -1.0), np.where(finite, -raw, -1.0)):
            result = result.astype(np.float32)
            _lo, score, _at, where = cv2.minMaxLoc(result)
            if score > best[0]:
                best = (float(score), where[0], where[1], size)
    return best


def _slot_scores(frame, hit, templates):
    height, width = frame.shape[:2]
    side = int(round(hit["h"] * height))
    cx, cy = int((hit["x"] + hit["w"] / 2) * width), int((hit["y"] + hit["h"] / 2) * height)
    reach = side // 2 + 10  # box is already placed; room for +/-4 size and a few px
    crop = cv2.cvtColor(frame[max(0, cy - reach) : cy + reach, max(0, cx - reach) : cx + reach], cv2.COLOR_BGR2GRAY)
    return {trait_id: _slot_best(crop, trait_id, alpha, side)[0] for trait_id, alpha in templates}


def verify_slots(frame, hits, templates):
    """Score every trait on each reported badge, glyph-masked, right where it sits.
    The reported id has to win there. Field 3 (winnishko, Russian client): a Hunter
    badge was reported as Eclipse (0.70 there vs Hunter 0.83). Across 1285 field
    hits every other one led the runner-up by >= 0.09. If another trait wins, it
    replaces the hit when it clears 0.72 and leads by SLOT_GAP; otherwise drop."""
    jobs = [_VERIFY_POOL.submit(_slot_scores, frame, hit, templates) for hit in hits]
    kept = []
    for hit, job in zip(hits, jobs):
        scores = job.result()
        own = scores.get(hit["id"], -1.0)
        other_id, other = max(((t, v) for t, v in scores.items() if t != hit["id"]), key=lambda item: item[1])
        if other <= own:
            kept.append(hit)
        elif other >= THRESHOLD and other - own >= SLOT_GAP and other_id not in {h["id"] for h in hits}:
            kept.append(dict(hit, id=other_id, score=round(other, 3)))
    return kept


MASK_THREADS = 4
_MASK_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=MASK_THREADS)


def _masked_start(frame, templates, x0, x1, skip):
    """Start the glyph-masked search early, one trait per task, while the band
    passes run. Traits the column already has are skipped; the band's finds are
    dropped later in _masked_pass, so the result matches the serial order."""
    return {
        trait_id: _MASK_POOL.submit(_band_found, frame, [(trait_id, alpha)], x0, x1, RECHECK_STEP, True)
        for trait_id, alpha in templates
        if trait_id not in skip
    }


def _masked_pass(frame, templates, x0, x1, have, started):
    """Glyph-masked hits for traits still missing. Same chunks and overlap picks
    as one masked pass per chunk (rest[i::MASK_THREADS]), so results are equal."""
    height, width = frame.shape[:2]
    rest = [(t, a) for t, a in templates if t not in have]
    if not rest:
        return []
    chunks = [rest[i::MASK_THREADS] for i in range(MASK_THREADS)]
    parts = [_band_keep([f for t, _a in part for f in started[t].result()], frame, x0) for part in chunks]
    hits = [h for part in parts for h in part]
    hits.sort(key=lambda h: -h["score"])
    kept = []
    for h in hits:
        box = (h["x"], h["y"], h["x"] + h["w"], h["y"] + h["h"])
        if any(iou(box, (k["x"], k["y"], k["x"] + k["w"], k["y"] + k["h"])) > 0.3 for k in kept):
            continue
        kept.append(h)
    return one_column(kept, width / height)


BAND_THREADS = 4
_BAND_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=BAND_THREADS)


def _match_band(frame, templates, x0, x1, step=SEARCH_STEP, masked=False, scores=None):
    return _band_keep(_band_found(frame, templates, x0, x1, step, masked, scores), frame, x0)


def _band_found(frame, templates, x0, x1, step=SEARCH_STEP, masked=False, scores=None):
    """Each trait's accepted peak in the band, before overlap suppression.
    scores, if given, gets every trait's first coarse peak (sequence mode)."""
    roi = cv2.cvtColor(frame[:, x0:x1], cv2.COLOR_BGR2GRAY)
    coarse = _down(roi, step)
    recheck = []

    def one(trait_id, alpha):
        best = _search(coarse, trait_id, alpha, step, masked)
        if best is None:
            return None
        if scores is not None:
            scores[trait_id] = best[0]
        score, second, x, y, w, h = best
        if not _accepts(score, second):
            if score < NEAR_SCORE or score - second < STRONG_GAP:
                return None
            if not recheck:
                recheck.append(_down(roi, RECHECK_STEP))
            best = _search(recheck[0], trait_id, alpha, RECHECK_STEP)
            if best is None or not _accepts(best[0], best[1]):
                return None
            score, second, x, y, w, h = best
        return (score, trait_id, x, y, w, h)

    # Each trait is scored on its own, so the traits can run side by side
    # (OpenCV drops the GIL). Results are gathered in template order, so the
    # output is the same as the serial loop. Single-trait calls stay serial.
    if len(templates) > 1:
        results = list(_BAND_POOL.map(lambda item: one(*item), templates))
    else:
        results = [one(trait_id, alpha) for trait_id, alpha in templates]
    return [r for r in results if r is not None]


def _band_keep(found, frame, x0):
    height, width = frame.shape[:2]
    found = sorted(found, reverse=True)
    kept = []
    for score, trait_id, x, y, w, h in found:
        box = (x, y, x + w, y + h)
        if any(iou(box, (k[2], k[3], k[2] + k[4], k[3] + k[5])) > 0.3 for k in kept):
            continue
        kept.append((score, trait_id, x, y, w, h))
    kept.sort(key=lambda item: item[3])
    return [
        {
            "id": trait_id,
            "x": (x + x0) / width,
            "y": y / height,
            "w": w / width,
            "h": h / height,
            "score": round(float(score), 3),
        }
        for score, trait_id, x, y, w, h in kept
    ]


def match_gray(frame, templates, origin=(0, 0), full_size=None, scales=AUGMENT_SCALES, color=False, threshold=THRESHOLD):
    """Match icon templates inside a crop. origin is the crop's top-left on the full frame.

    color=True matches BGR against BGR. Tiers I/II share a shape and differ in
    tint: on jazlatte 4-2, 治癒靈球I vs II scored 0.814/0.816 in gray and
    0.805/0.691 in color.
    """
    height, width = full_size or frame.shape[:2]
    ox, oy = origin
    gray = frame if color else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    found = []
    for augment_id, image in templates:
        best = None
        for side in scales:
            if side >= gray.shape[0] or side >= gray.shape[1]:
                continue
            key = ("augment", augment_id, side, color)
            template = _SCALED.get(key)
            if template is None:
                template = image if color or image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                template = cv2.resize(template, (side, side), interpolation=cv2.INTER_AREA)
                _SCALED[key] = template
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _min, score, _min_at, where = cv2.minMaxLoc(result)
            if best is None or score > best[0]:
                best = (float(score), where[0], where[1], side, side)
        if best and best[0] >= threshold:
            score, x, y, w, h = best
            found.append((score, augment_id, x + ox, y + oy, w, h))
    found.sort(reverse=True)
    kept = []
    for score, augment_id, x, y, w, h in found:
        box = (x, y, x + w, y + h)
        if any(iou(box, (k[2], k[3], k[2] + k[4], k[3] + k[5])) > 0.3 for k in kept):
            continue
        kept.append((score, augment_id, x, y, w, h))
    kept.sort(key=lambda item: item[2])
    return [
        {
            "id": augment_id,
            "x": x / width,
            "y": y / height,
            "w": w / width,
            "h": h / height,
            "score": round(float(score), 3),
        }
        for score, augment_id, x, y, w, h in kept
    ]


# 16:9 select cards at 1920x1080: the band that holds the three glyphs (demo crop).
# Three card windows. Glyph x on real streams: 475-487, 881-890, 1280-1300
# (kiyoon 3-2, jazlatte 4-2, ariasaki 2-1); y 362-372. The demo card sits at 502/910/1321, 364.
SLOT_CARDS = ((440, 330, 660, 540), (850, 330, 1070, 540), (1250, 330, 1480, 540))
# Card glyphs on real 1920x1080 streams are 136-152 px (the 128 px icon with its
# rim); 96 stays for the synthetic demo card.
CARD_SCALES = (96, 136, 144, 152)
# Top-left selected bar at 1920x1080, glyphs 30-42 px. Measured on real frames
# (2026-10-21): true bar icons 0.83-0.88 (jazlatte, kiyoon), no-bar frames <= 0.57,
# but a choice-card glyph on stage-6-1 scored Golemify 0.747. So this one region
# gates at 0.80 instead of 0.72; every other region keeps 0.72.
SELECTED_BAR = (440, 200, 620, 290)
BAR_SCALES = (30, 34, 38, 42)
BAR_THRESHOLD = 0.80


def match_slots(frame, templates):
    """Augments on a 16:9 frame: the three choice cards. Other ratios stay silent."""
    height, width = frame.shape[:2]
    if not templates or abs(width / height - 16 / 9) > 0.02:
        return []
    if (width, height) != (1920, 1080):
        frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_AREA if width > 1920 else cv2.INTER_CUBIC)
    regions = [(r, CARD_SCALES, THRESHOLD) for r in SLOT_CARDS]
    if SELECTED_BAR:
        regions.append((SELECTED_BAR, BAR_SCALES, BAR_THRESHOLD))
    def one(region):
        (x0, y0, x1, y1), scales, gate = region
        crop = frame[y0:y1, x0:x1]
        shortlist = _slot_shortlist(crop, templates, scales)
        found = match_gray(crop, shortlist, origin=(x0, y0), full_size=(1080, 1920), scales=scales, color=True, threshold=gate)
        found = [hit for hit in found if not _tie_against_color(hit, crop, (x0, y0), shortlist, scales)]
        return crop, scales, shortlist, found

    # The four regions are independent; OpenCV drops the GIL, so score them side
    # by side. Results are gathered in region order: same output as the loop.
    hits = []
    cards = []
    for crop, scales, shortlist, found in _SLOT_POOL.map(one, regions):
        hits.extend(found)
        if scales is CARD_SCALES:
            cards.extend((hit, crop, shortlist) for hit in found)
    narrow_by_round(cards)
    return hits


# Near tie between two icon families (I vs II, silver vs prismatic): same shape,
# the tint differs. On the 702 field frames 8 hits led another family by < 0.02;
# in 7 the per-pixel a/b color agreed with the pick, in 1 (mojoko_go 3-2: 神偷軍團 I
# on screen, II 0.847 vs I 0.840) the rival's color was closer by 5.2. A tie the
# color does not back stays silent instead of naming a guess.
TIE_GAP = 0.02
TIE_COLOR = 3.0


def _ab_distance(patch, image, side):
    template = cv2.resize(image, (side, side), interpolation=cv2.INTER_AREA)
    mask = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) > 60
    if patch.shape[:2] != (side, side) or not mask.any():
        return None
    a = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB).astype(np.float32)[mask][:, 1:]
    b = cv2.cvtColor(template, cv2.COLOR_BGR2LAB).astype(np.float32)[mask][:, 1:]
    return float(np.linalg.norm(a - b, axis=1).mean())


def _tie_against_color(hit, crop, origin, shortlist, scales):
    groups = augment_rounds()[1]
    family = set(groups.get(hit["id"]) or [hit["id"]])
    width, height = 1920, 1080
    x, y = round(hit["x"] * width), round(hit["y"] * height)
    side = round(hit["w"] * width)
    box = (x, y, x + side, y + side)
    rival = None
    for other, image in shortlist:
        if other in family:
            continue
        for got in match_gray(crop, [(other, image)], origin=origin, full_size=(height, width), scales=scales, color=True, threshold=-1.0):
            gx, gy = got["x"] * width, got["y"] * height
            if iou(box, (gx, gy, gx + got["w"] * width, gy + got["h"] * height)) > 0.3 and (rival is None or got["score"] > rival[1]):
                rival = (image, got["score"])
    if rival is None or hit["score"] - rival[1] >= TIE_GAP:
        return False
    images = dict(shortlist)
    ox, oy = origin
    patch = crop[y - oy : y - oy + side, x - ox : x - ox + side]
    mine = _ab_distance(patch, images[hit["id"]], side)
    theirs = _ab_distance(patch, rival[0], side)
    return mine is not None and theirs is not None and theirs + TIE_COLOR < mine


# Pick rounds per augment (1 = 2-1, 2 = 3-2, 3 = 4-2), only where two sources
# agree (data/augment_rounds.json). Same-icon variants differ by round: 特性神木
# only at 2-1, 特性神木+ only at 3-2. The three cards on screen are one pick, so
# a card whose icon has one known round set fixes the pick for the others.
# The selected bar is not used: a Destiny augment adds a bonus icon to it
# (recls_tft: four icons), so bar order or count does not give the pick.
ROUNDS_FILE = DATA / "augment_rounds.json"
# A narrowed card must beat every other icon family on its crop by this much.
# mojoko_go 3-2: 神偷軍團 (I) on screen, II 0.847 vs I 0.840; no narrowing there.
ROUND_LEAD = 0.05
_ROUNDS = {}
_ROUNDS_LOCK = threading.Lock()


def augment_rounds():
    # Slot regions run in threads: fill both keys at once so a racing reader
    # never sees "rounds" without "groups".
    with _ROUNDS_LOCK:
        if "groups" not in _ROUNDS:
            try:
                rounds = json.loads(ROUNDS_FILE.read_text(encoding="utf-8")).get("rounds") or {}
            except (OSError, ValueError):
                rounds = {}
            _ROUNDS.update(rounds=rounds, groups=same_icon_groups())
    return _ROUNDS["rounds"], _ROUNDS["groups"]


def _family_rounds(augment_id, rounds, groups):
    """Rounds the icon can be shown at, or None if any member is unknown."""
    members = groups.get(augment_id) or [augment_id]
    got = set()
    for member in members:
        if member not in rounds:
            return None
        got |= set(rounds[member])
    return got


def _lead(hit, crop, shortlist, groups):
    family = set(groups.get(hit["id"]) or [hit["id"]])
    others = [(i, image) for i, image in shortlist if i not in family]
    if not others:
        return 1.0
    rivals = match_gray(crop, others, scales=CARD_SCALES, color=True, threshold=-1.0)
    best_other = max((r["score"] for r in rivals), default=-1.0)
    return hit["score"] - best_other


def narrow_by_round(cards):
    """Replace a same-icon card id with its one variant offered at this pick."""
    if len(cards) < 2:
        return
    rounds, groups = augment_rounds()
    if not rounds:
        return
    pick = {1, 2, 3}
    for hit, _crop, _shortlist in cards:
        members = groups.get(hit["id"]) or [hit["id"]]
        if len(members) > 1:
            continue
        known = _family_rounds(hit["id"], rounds, groups)
        if known:
            pick &= known
    if len(pick) != 1:
        return
    (now,) = pick
    for hit, crop, shortlist in cards:
        members = groups.get(hit["id"]) or []
        if len(members) < 2 or any(m not in rounds for m in members):
            continue
        offered = [m for m in members if now in rounds[m]]
        if len(offered) != 1 or _lead(hit, crop, shortlist, groups) < ROUND_LEAD:
            continue
        hit["id"] = offered[0]
        hit["exact"] = True


SLOT_SHORTLIST = 6
_SLOT_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=4)
SHORTLIST_STEP = 4


_SHORTLIST_BANK = {}


def _shortlist_bank(templates, small):
    """Every glyph at one size, mean-removed and stacked as columns for one BLAS product."""
    key = (id(templates), len(templates), small)
    hit = _SHORTLIST_BANK.get(key)
    if hit is None:
        stack = np.stack([
            cv2.resize(image, (small, small), interpolation=cv2.INTER_AREA).astype(np.float64)
            for _augment_id, image in templates
        ])
        stack -= stack.mean(axis=(1, 2), keepdims=True)
        flat = stack.reshape(len(templates), -1)
        hit = (flat.T.copy(), np.sqrt((flat ** 2).sum(axis=1)), templates)
        _SHORTLIST_BANK[key] = hit
    return hit


def _slot_shortlist(crop, templates, scales=CARD_SCALES):
    """Rank every glyph at 1/4, keep the best few. The 0.72 gate runs at full size after.

    Same TM_CCOEFF_NORMED score as cv2.matchTemplate, but all glyphs of one size are scored
    in a single matrix product over the crop's sliding windows instead of ~180 small calls.
    """
    gray = _down(crop, SHORTLIST_STEP).astype(np.float64)
    if gray.ndim == 2:
        gray = gray[:, :, None]
    best = np.full(len(templates), -1.0)
    for side in scales:
        small = side // SHORTLIST_STEP
        if small >= gray.shape[0] or small >= gray.shape[1]:
            continue
        columns, norms, _keep = _shortlist_bank(templates, small)
        windows = np.lib.stride_tricks.sliding_window_view(gray, (small, small, gray.shape[2]))[:, :, 0]
        patches = windows.reshape(-1, small, small, gray.shape[2])
        patches = patches - patches.mean(axis=(1, 2), keepdims=True)
        flat = patches.reshape(len(patches), -1)
        denom = np.sqrt((flat ** 2).sum(axis=1))[:, None] * norms[None, :]
        score = np.where(denom > 1e-9, (flat @ columns) / np.maximum(denom, 1e-12), 0.0)
        best = np.maximum(best, score.max(axis=0))
    order = sorted(range(len(templates)), key=lambda i: -best[i])
    return [templates[i] for i in order[: SLOT_SHORTLIST]]


def iou(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    inter = max(0, ix1 - ix0) * max(0, iy1 - iy0)
    if inter == 0:
        return 0
    area = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / area


# Some augments ship a placeholder icon in CDragon (hexcore/missing-t1/t2: a plain "T";
# 2026-10-23 every set-18 trait augment) while the HUD draws real art, so they never
# matched. data/augments_hud holds that art cut from real frames and wins over the
# CDragon icon, as data/icons_hud does for traits. fetch does not touch it.
AUGMENTS_HUD = DATA / "augments_hud"


def load_bgr(augment_id):
    path = AUGMENTS_HUD / f"{augment_id}.png"
    if not path.is_file():
        path = DATA / "augments" / f"{augment_id}.png"
    return cv2.imread(str(path), cv2.IMREAD_COLOR)


# Many augments share one icon (tiers I/II/III, Plus, the same augment from an
# older set). The icon cannot tell them apart, so one template stands for the
# group. On kiyoon's 3-2 card (2026-10-21) the card text matched the DA_ copy
# for both shared icons (5 gold, 4%), so DA_ members win when a group has them.
# More than MAX_SAME_ICON candidates is not an answer; that icon stays silent.
MAX_SAME_ICON = 4


def _augment_images():
    import hashlib

    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    groups = {}
    for augment_id in payload.get("augments") or {}:
        if not (DATA / "augments" / f"{augment_id}.png").is_file():
            continue
        image = load_bgr(augment_id)
        if image is None:
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if int(gray.max()) - int(gray.min()) < 8:
            continue
        key = hashlib.sha1(image.tobytes()).hexdigest()
        groups.setdefault(key, (image, []))[1].append(augment_id)
    return groups


def same_icon_groups():
    """rep id -> every augment the screen could be showing. Silent groups map to []."""
    out = {}
    for _gray, members in _augment_images().values():
        if len(members) < 2:
            continue
        current = [m for m in members if m.startswith("DA_")] or members
        current.sort()
        out[current[0]] = current if len(current) <= MAX_SAME_ICON else []
    return out


def load_augment_templates():
    templates = []
    for gray, members in _augment_images().values():
        current = sorted([m for m in members if m.startswith("DA_")] or members)
        if len(current) > MAX_SAME_ICON:
            continue
        templates.append((current[0], gray))
    return templates


def paint_bgr(frame, image, x, y, side):
    frame[y : y + side, x : x + side] = cv2.resize(image, (side, side), interpolation=cv2.INTER_AREA)


def build_frame(catalog):
    """A 16:9 stand-in: trait column on the left, three augment icons on the select cards."""
    chosen = [
        "DA_18_Elderwood",
        "DA_18_Coven",
        "DA_18_Solar",
        "DA_18_Hunter",
        "DA_18_Defender",
        "DA_18_Eclipse",
    ]
    frame = np.full((1080, 1920, 3), (18, 22, 14), np.uint8)
    planted = {}
    y = 150
    for trait_id in chosen:
        alpha = load_alpha(trait_id)
        side = 40
        x = 48
        paint(frame, alpha, x, y, side)
        planted[trait_id] = (x, y, side, side)
        y += 78
    planted_augments = {}
    for augment_id, x, y in AUGMENT_SLOT:
        image = load_bgr(augment_id)
        if image is None:
            raise SystemExit(f"missing augment icon {augment_id}")
        paint_bgr(frame, image, x, y, AUGMENT_SIDE)
        planted_augments[augment_id] = (x, y, AUGMENT_SIDE, AUGMENT_SIDE)
    DATA.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DATA / "frame.png"), frame)
    return frame, planted, planted_augments


def bind_target(host):
    if host in ("0.0.0.0", "::", ""):
        return "127.0.0.1"
    return host


def capture_main(shot):
    """Grab the main display. The served picture is this file, not a crop of it."""
    shot.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(["screencapture", "-x", "-m", str(shot)], check=False)
    if completed.returncode != 0 or not shot.is_file():
        return None
    return cv2.imread(str(shot))


def roi_digest(frame):
    width = frame.shape[1]
    roi = frame[:, : max(1, int(width * ROI_FRACTION))]
    return hashlib.sha256(np.ascontiguousarray(roi)).hexdigest()


def watch(host="127.0.0.1", port=8765, ebs="", ebs_token=""):
    """Capture the main display and match traits.

    The local page shows the capture for alignment. The broadcast, when --ebs
    is set, is only ids and boxes. Augment cards are not posted. An unchanged
    left column skips the match. One pass is about a second.
    ponytail: the grab stays full-frame and synchronous. A left strip would
    publish boxes against the strip width, and the match already hides the grab.
    """
    import time

    import relay

    ensure_catalog()
    try:
        httpd = relay.serve(host, port)
    except OSError as exc:
        raise SystemExit(f"port {port} is in use: {exc}") from exc
    templates = load_templates()
    names = traits_of(json.loads(CATALOG.read_text(encoding="utf-8")))
    bound = httpd.server_address[1]
    token = broadcast_token(ebs, ebs_token)
    print(f"本機除錯 http://127.0.0.1:{bound}/", flush=True)
    print("這一頁只在這台電腦，用來對截圖。正式路徑不送圖。", flush=True)
    if ebs:
        print(f"廣播 {ebs}", flush=True)
    shot = DATA / "capture.png"
    warned = False
    seen = None
    while True:
        frame = capture_main(shot)
        if frame is None:
            print("抓不到主螢幕", flush=True)
            time.sleep(2)
            continue
        digest = roi_digest(frame)
        if digest == seen:
            os.replace(shot, DATA / "frame.png")
            print("不變", flush=True)
            time.sleep(0.5)
            continue
        hits = match(frame, templates)
        os.replace(shot, DATA / "frame.png")
        seen = digest
        post(hits, bound, host, httpd.token)
        if ebs:
            try:
                push_ebs(hits, ebs, token, int(time.time() * 1000))
            except OSError as exc:
                if not warned:
                    print(f"廣播沒送出：{exc}", flush=True)
                    warned = True
            else:
                warned = False
        labels = [names.get(hit["id"], {}).get("name", hit["id"]) for hit in hits]
        print(f"{len(hits)} {' '.join(labels)}", flush=True)


def live_update(hits, when_ms):
    """Ids and normalized boxes only. The viewer already has the words."""
    boxes = [
        {"id": hit["id"], "x": float(hit["x"]), "y": float(hit["y"]), "w": float(hit["w"]), "h": float(hit["h"])}
        for hit in hits
    ]
    return {"type": "update", "t": int(when_ms), "boxes": boxes}


def broadcast_token(url, explicit="", root=DATA):
    """Local ebs and the public relay keep different tokens."""
    if explicit:
        return explicit
    name = "relay.token" if str(url).startswith(("https://", "wss://")) else "ebs.token"
    path = root / name
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


def push_ebs(hits, url, token, when_ms):
    body = json.dumps(live_update(hits, when_ms)).encode()
    # workers.dev rejects Python's default user agent.
    req = urllib.request.Request(
        url.rstrip("/") + "/push",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "tft-trait-hover",
        },
    )
    with urllib.request.urlopen(req, timeout=2) as response:
        response.read()


def post(hits, port, host="127.0.0.1", token=""):
    body = json.dumps({"hits": hits}).encode()
    req = urllib.request.Request(
        f"http://{bind_target(host)}:{port}/state",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        response.read()


def demo(host="127.0.0.1", port=8765):
    import relay

    ensure_catalog()
    catalog = traits_of(json.loads(CATALOG.read_text(encoding="utf-8")))
    frame, planted, planted_augments = build_frame(catalog)
    hits = match(frame, load_templates())
    crop = frame[340:480, 480:1460]
    hits.extend(
        match_gray(
            crop,
            load_augment_templates(),
            origin=(480, 340),
            full_size=frame.shape[:2],
        )
    )
    got = {hit["id"] for hit in hits}
    expect = set(planted) | set(planted_augments)
    if got != expect:
        raise SystemExit(f"match {sorted(got)} != planted {sorted(expect)}")
    height, width = frame.shape[:2]
    boxes = {**planted, **planted_augments}
    for hit in hits:
        x, y, side, _side = boxes[hit["id"]]
        if abs(hit["x"] * width - x) > 4 or abs(hit["y"] * height - y) > 4:
            raise SystemExit(f"box off for {hit['id']}: {hit}")
    allowed = {"id", "x", "y", "w", "h", "score"}
    leaked = [key for hit in hits for key in hit if key not in allowed]
    if leaked:
        raise SystemExit(f"live payload carries extra fields: {leaked}")
    httpd = relay.serve(host, port)
    bound = httpd.server_address[1]
    post(hits, bound, host, httpd.token)
    print(f"本機除錯 http://127.0.0.1:{bound}/", flush=True)
    print("這一頁只在這台電腦。", flush=True)
    print(f"token {httpd.token}", flush=True)
    return bound


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="companion.py")
    parser.add_argument(
        "command", nargs="?", default="demo", choices=("fetch", "demo", "check", "watch")
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--ebs", default="")
    parser.add_argument("--ebs-token", default="")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv[1:])
    if args.command == "fetch":
        fetch()
        print("fetch 完成", flush=True)
        return
    elif args.command == "check":
        import check

        raise SystemExit(check.main())
    try:
        if args.command == "watch":
            watch(args.host, args.port, args.ebs, args.ebs_token)
        else:
            import threading

            demo(args.host, args.port)
            threading.Event().wait()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main(sys.argv)
