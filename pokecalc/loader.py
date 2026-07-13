"""讀取 data/ 的本地快照,並提供繁中名稱查詢。"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

_cache = {}


def _load(name):
    if name not in _cache:
        with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
            _cache[name] = json.load(f)
    return _cache[name]


def pokemon():
    return _load("pokemon.json")


def moves():
    return _load("moves.json")


def names():
    return _load("names_zh_tw.json")


def meta():
    try:
        return _load("meta.json")
    except FileNotFoundError:
        return {}


def zh_pokemon(mon):
    """回傳寶可夢繁中顯示名(含形態標籤)。完整名稱覆寫表優先。"""
    from i18n import POKEMON_NAME_OVERRIDES
    uid = mon["uid"]
    base_uid = uid[:-7] if uid.endswith("_SHADOW") else uid
    override = POKEMON_NAME_OVERRIDES.get(base_uid)
    if override:
        return ("暗影" + override) if mon["is_shadow"] else override
    nm = names()
    base = nm["pokemon"].get(mon["pokemon_id"], mon["name_en"])
    form = mon.get("form")
    if not form:
        return base
    # 形態逐段翻譯(SHADOW / MEGA_X / ALOLA ...)
    parts = []
    for seg in form.split("_"):
        parts.append(nm["form"].get(seg, seg.title()))
    label = "".join(p for p in parts if p)
    return f"{label}{base}" if label else base


def zh_move(move_id):
    return names()["move"].get(move_id, en_move(move_id))


def en_move(move_id):
    """招式英文名(由招式 id 推得,如 FIRE_SPIN_FAST → Fire Spin)。"""
    return move_id.replace("_FAST", "").replace("_", " ").title()


# GO 風格圖示(pokemon-resources,經 jsDelivr CDN,含各形態)
_POGO_SPRITE_BASE = "https://cdn.jsdelivr.net/gh/mgrann03/pokemon-resources@main/graphics/pogo-256"
# 回退:官方美術圖(依圖鑑編號)
_FALLBACK_SPRITE_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"


def sprite_url(mon):
    """回傳寶可夢圖片 URL(需連網;離線時圖片不顯示但不影響功能)。"""
    if mon.get("sprite"):
        return f"{_POGO_SPRITE_BASE}/{mon['sprite']}"
    return f"{_FALLBACK_SPRITE_BASE}/{mon['dex']}.png"
