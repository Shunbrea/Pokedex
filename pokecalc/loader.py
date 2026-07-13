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


OVERRIDES_PATH = os.path.join(DATA_DIR, "overrides.json")


def overrides():
    """本地覆寫(data/overrides.json):補招式、修 released。檔案不存在回傳空結構。

    key 為寶可夢 uid;暗影變體查不到時回退本體 uid(去 _SHADOW 後綴)。
    """
    if "overrides" not in _cache:
        try:
            with open(OVERRIDES_PATH, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        _cache["overrides"] = {
            "add_moves": data.get("add_moves", {}),
            "released": data.get("released", {}),
        }
    return _cache["overrides"]


def overrides_token():
    """overrides.json 的 mtime,供跨模組快取(如排名表)當失效 key。"""
    try:
        return os.path.getmtime(OVERRIDES_PATH)
    except OSError:
        return 0.0


def _apply_overrides(mon, ov, valid_moves):
    """回傳套用覆寫後的寶可夢條目(淺複本;原始資料不動)。"""
    uid = mon["uid"]
    base_uid = uid[:-7] if uid.endswith("_SHADOW") else uid
    keys = [uid] if uid == base_uid else [uid, base_uid]

    e = dict(mon)
    for key in keys:
        add = ov["add_moves"].get(key)
        if add:
            for field in ("fast", "charged", "elite_fast", "elite_charged"):
                ids = [m for m in add.get(field, []) if m in valid_moves]
                if ids:
                    e[field] = sorted(set(e.get(field, [])) | set(ids))
    for key in keys:  # uid 優先於本體 uid
        if key in ov["released"]:
            e["released"] = bool(ov["released"][key])
            break
    return e


def pokemon():
    """寶可夢清單(已套用 data/overrides.json 的本地覆寫)。"""
    if "pokemon" not in _cache:
        ov = overrides()
        mv = moves()
        _cache["pokemon"] = [_apply_overrides(m, ov, mv) for m in _load("pokemon.json")]
    return _cache["pokemon"]


def set_released_override(uid: str, released: bool):
    """寫入/移除某 uid 的 released 覆寫(與上游值相同時移除),並清除快取。"""
    src = next((m["released"] for m in _load("pokemon.json") if m["uid"] == uid), None)
    try:
        with open(OVERRIDES_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    rel = data.setdefault("released", {})
    if src is not None and bool(released) == bool(src):
        rel.pop(uid, None)
    else:
        rel[uid] = bool(released)
    with open(OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    _cache.pop("overrides", None)
    _cache.pop("pokemon", None)


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
