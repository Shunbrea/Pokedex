"""枚舉全部寶可夢 × 招式組合,產出排行(pandas DataFrame)。"""

import pandas as pd

from . import calc, loader

# 排名表欄位結構版本:欄位增減時 +1,讓 UI 層的 st.cache_data 舊快取失效
# (Streamlit 熱重載不會清記憶體快取,否則會拿到缺新欄位的舊 DataFrame)
SCHEMA_VERSION = 2


def _usable_moves(mon, s: calc.Settings):
    """回傳(可用快招 id 清單, 可用充能招 id 清單),依 legacy 設定納入菁英招式。"""
    fast = list(mon["fast"])
    charged = list(mon["charged"])
    if s.include_legacy:
        fast += mon.get("elite_fast", [])
        charged += mon.get("elite_charged", [])
    return sorted(set(fast)), sorted(set(charged))


def top_movesets(mon, s: calc.Settings, moves, move_type=None):
    """回傳該寶可夢依 eDPS 排序的前 N 組(快招, 充能招)與指標。

    move_type 不為 None 時(分屬性榜):
      - 充能招屬性必須 == move_type,並對該屬性招式套效果絕佳倍率(單一弱點模型)
      - allow_mixed=False 時,快招屬性也必須 == move_type
    """
    fast_ids, charge_ids = _usable_moves(mon, s)
    results = []
    for cid in charge_ids:
        cm = moves.get(cid)
        if not cm:
            continue
        if move_type and cm["type"] != move_type:
            continue
        for fid in fast_ids:
            fm = moves.get(fid)
            if not fm:
                continue
            if move_type and not s.allow_mixed and fm["type"] != move_type:
                continue
            r = calc.evaluate(mon, fm, cm, s, boost_type=move_type)
            if r["edps"] > 0:
                results.append({**r, "fast": fid, "charge": cid})
    results.sort(key=lambda r: r["edps"], reverse=True)
    return results[:max(1, s.movesets_per_pokemon)]


def _eligible(mon, s: calc.Settings, move_type=None):
    if mon["is_mega"] and not s.include_mega:
        return False
    if mon["is_shadow"] and not s.include_shadow:
        return False
    if not mon.get("released", True) and not s.include_unreleased:
        return False
    # 分屬性榜:只列本身具有該屬性的寶可夢(STAB 必有)
    if move_type and s.require_type and move_type not in mon["types"]:
        return False
    return True


def build_ranking(s: calc.Settings, move_type=None):
    """產出排行 DataFrame(已排序、附 Tier 與排名)。

    move_type:限定充能招屬性並套效果絕佳倍率(分屬性榜);None 為整體中性榜。
    """
    mons = loader.pokemon()
    moves = loader.moves()

    rows = []
    for mon in mons:
        if not _eligible(mon, s, move_type):
            continue
        for b in top_movesets(mon, s, moves, move_type):
            rows.append({
                "uid": mon["uid"],
                "dex": mon["dex"],
                "name": loader.zh_pokemon(mon),
                "name_en": mon["name_en"],
                "sprite": loader.sprite_url(mon),
                "types": mon["types"],
                "fast": loader.zh_move(b["fast"]),
                "fast_en": loader.en_move(b["fast"]),
                "fast_type": moves[b["fast"]]["type"],
                "fast_elite": b["fast"] in mon.get("elite_fast", []),
                "charge": loader.zh_move(b["charge"]),
                "charge_en": loader.en_move(b["charge"]),
                "charge_type": moves[b["charge"]]["type"],
                "charge_elite": b["charge"] in mon.get("elite_charged", []),
                "dps": b["dps"],
                "tdo": b["tdo"],
                "edps": b["edps"],
                "faints": b["faints"],
                "ttw": b["ttw"],
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values("edps", ascending=False).reset_index(drop=True)

    top = df["edps"].iloc[0]
    is_type_page = move_type is not None
    df["tier"] = df["edps"].apply(
        lambda e: calc.assign_tier(e, top, s.tier_method, is_type_page, s.type_se_mult))
    df.insert(0, "rank", range(1, len(df) + 1))
    return df
