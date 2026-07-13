"""屬性相剋表(Pokemon GO 數值)。

倍率:效果絕佳 1.6、效果不好 0.625、無效果/雙重抵抗 0.390625、一般 1.0。
"""

SE = 1.6          # super effective
NVE = 0.625       # not very effective
IMMUNE = 0.390625  # Pokemon GO 沒有完全免疫,以 0.625^2 表示

TYPES = [
    "NORMAL", "FIRE", "WATER", "ELECTRIC", "GRASS", "ICE", "FIGHTING", "POISON",
    "GROUND", "FLYING", "PSYCHIC", "BUG", "ROCK", "GHOST", "DRAGON", "DARK",
    "STEEL", "FAIRY",
]

# 每個攻擊屬性:(效果絕佳的防禦屬性, 效果不好的防禦屬性, 無效果的防禦屬性)
_REL = {
    "NORMAL":   ([], ["ROCK", "STEEL"], ["GHOST"]),
    "FIRE":     (["GRASS", "ICE", "BUG", "STEEL"], ["FIRE", "WATER", "ROCK", "DRAGON"], []),
    "WATER":    (["FIRE", "GROUND", "ROCK"], ["WATER", "GRASS", "DRAGON"], []),
    "ELECTRIC": (["WATER", "FLYING"], ["ELECTRIC", "GRASS", "DRAGON"], ["GROUND"]),
    "GRASS":    (["WATER", "GROUND", "ROCK"], ["FIRE", "GRASS", "POISON", "FLYING", "BUG", "DRAGON", "STEEL"], []),
    "ICE":      (["GRASS", "GROUND", "FLYING", "DRAGON"], ["FIRE", "WATER", "ICE", "STEEL"], []),
    "FIGHTING": (["NORMAL", "ICE", "ROCK", "DARK", "STEEL"], ["POISON", "FLYING", "PSYCHIC", "BUG", "FAIRY"], ["GHOST"]),
    "POISON":   (["GRASS", "FAIRY"], ["POISON", "GROUND", "ROCK", "GHOST"], ["STEEL"]),
    "GROUND":   (["FIRE", "ELECTRIC", "POISON", "ROCK", "STEEL"], ["GRASS", "BUG"], ["FLYING"]),
    "FLYING":   (["GRASS", "FIGHTING", "BUG"], ["ELECTRIC", "ROCK", "STEEL"], []),
    "PSYCHIC":  (["FIGHTING", "POISON"], ["PSYCHIC", "STEEL"], ["DARK"]),
    "BUG":      (["GRASS", "PSYCHIC", "DARK"], ["FIRE", "FIGHTING", "POISON", "FLYING", "GHOST", "STEEL", "FAIRY"], []),
    "ROCK":     (["FIRE", "ICE", "FLYING", "BUG"], ["FIGHTING", "GROUND", "STEEL"], []),
    "GHOST":    (["PSYCHIC", "GHOST"], ["DARK"], ["NORMAL"]),
    "DRAGON":   (["DRAGON"], ["STEEL"], ["FAIRY"]),
    "DARK":     (["PSYCHIC", "GHOST"], ["FIGHTING", "DARK", "FAIRY"], []),
    "STEEL":    (["ICE", "ROCK", "FAIRY"], ["FIRE", "WATER", "ELECTRIC", "STEEL"], []),
    "FAIRY":    (["FIGHTING", "DRAGON", "DARK"], ["FIRE", "POISON", "STEEL"], []),
}

# 展開成 CHART[攻擊屬性][防禦屬性] = 倍率
CHART = {atk: {d: 1.0 for d in TYPES} for atk in TYPES}
for atk, (se, nve, imm) in _REL.items():
    for d in se:
        CHART[atk][d] = SE
    for d in nve:
        CHART[atk][d] = NVE
    for d in imm:
        CHART[atk][d] = IMMUNE


def effectiveness(move_type: str, defender_types) -> float:
    """招式屬性對(單或雙)防禦屬性的總倍率。"""
    mult = 1.0
    row = CHART.get(move_type, {})
    for dt in defender_types:
        mult *= row.get(dt, 1.0)
    return mult
