"""核心計算:傷害、DPS、TDO、eDPS、Faints、TTW、Tier。

模型對齊開源標準(DialgaDex,基於 GamePress「Comprehensive DPS」)。
公式中的常數集中在 Settings,可於介面即時調整:
    傷害/次 = dmg_coeff · 威力 · (攻擊/首領防禦) · STAB · 屬性倍率 · 天氣 + dmg_bonus
    DPS0    = (FDPS·CEPS + CDPS·FEPS) / (CEPS+FEPS)
    DPS     = DPS0 + (CDPS-FDPS)/(CEPS+FEPS) · (0.5 - x/HP) · y      (y = 受擊常數/防禦)
    TDO     = (HP/y) · DPS
    eDPS    = DPS·TDO / (TDO + DPS·重進/隊伍人數)                     (計入陣亡重進)
    Faints  = 首領HP/TDO      TTW = 首領HP/DPS
"""

from dataclasses import dataclass
from math import floor

from .cpm import cpm
from .typechart import effectiveness  # noqa: F401(_move_damage 使用)

IV = 15  # 攻擊手預設 IV 15/15/15
SHADOW_ATK_MULT = 1.2
SHADOW_DEF_MULT = 0.8333333

FRIENDSHIP = {
    "none": 1.0, "good": 1.03, "great": 1.05, "ultra": 1.07, "best": 1.10,
}
# 盟友 Mega 加成:同屬性 1.3、異屬性 1.1(此處以整體攻擊倍率近似)
MEGA_BOOST = {"none": 1.0, "diff": 1.1, "same": 1.3}

# 對齊 DialgaDex 的預設常數
DEFAULT_DEF_BOSS = 180.0
DEFAULT_INCOMING = 1970.0
DEFAULT_BOSS_HP = 15000.0
DEFAULT_STAB = 1.2
DEFAULT_WEATHER = 1.2
DEFAULT_TYPE_SE = 1.6      # 分屬性榜:效果絕佳倍率
DEFAULT_DMG_COEFF = 0.5
DEFAULT_DMG_BONUS = 0.5
DEFAULT_RELOBBY = 10.0
DEFAULT_TEAM = 6
DEFAULT_SWAP = 0.6   # 每次陣亡的換手延遲(秒);全隊滅團才付重進成本

# Tier 門檻 —— absolute 法(對全域尺度 eDPS;分屬性榜先 ÷效果絕佳倍率映回全域)
# 依本模型整體榜 eDPS 分佈校正,產生 SSSSS→C 的合理分佈
TIER_ABS = [(23.0, "SSSSS"), (21.0, "SSSS"), (19.0, "SSS"), (17.0, "SS"),
            (15.0, "S"), (13.0, "A"), (11.0, "B"), (0.0, "C")]
# Tier 門檻 —— ratio 法(對「eDPS/榜首eDPS」比例)
TIER_RATIO = [(0.9, "SSSSS"), (0.82, "SSSS"), (0.74, "SSS"),
              (0.66, "SS"), (0.55, "S"), (0.42, "A"), (0.0, "B")]


@dataclass
class Settings:
    # 基本
    level: int = 40
    weather: bool = False
    friendship: str = "none"
    party_size: int = 1            # Party Power:1=關,2/3/4 開
    mega_boost: str = "none"       # none/diff/same 盟友 Mega 加成
    include_mega: bool = True
    include_shadow: bool = True
    include_legacy: bool = True
    include_unreleased: bool = False   # 是否納入未實裝寶可夢/形態
    movesets_per_pokemon: int = 1      # 每隻寶可夢最多顯示幾組招式
    allow_mixed: bool = True           # 分屬性榜是否允許快招與榜屬性不同(混屬性招式組)
    require_type: bool = True          # 分屬性榜只列本身具有該屬性的寶可夢(STAB 必有)
    boss_types: tuple = ()             # 頭目屬性(主,次);空 = 關閉,倍率用固定 type_se_mult
    tier_method: str = "absolute"  # absolute / ratio
    # 公式細節(對齊 DialgaDex 預設)
    pve_turns: bool = True         # 招式時長取整到 0.5 秒(GO 團體戰回合制)
    one_bar_penalty: bool = True   # 一格充能招(-100 能量)陣亡能量浪費懲罰
    death_energy_waste: bool = True  # 陣亡時損失被打累積的能量(懲罰脆皮)
    boss_cm_power: float = 11670.0   # 首領充能招威力常數(陣亡能量浪費項用)
    # 公式常數(可調)
    def_boss: float = DEFAULT_DEF_BOSS
    incoming_const: float = DEFAULT_INCOMING
    boss_hp: float = DEFAULT_BOSS_HP
    stab: float = DEFAULT_STAB
    weather_mult: float = DEFAULT_WEATHER
    type_se_mult: float = DEFAULT_TYPE_SE
    dmg_coeff: float = DEFAULT_DMG_COEFF
    dmg_bonus: float = DEFAULT_DMG_BONUS
    relobby: float = DEFAULT_RELOBBY
    team_size: int = DEFAULT_TEAM
    swap_time: float = DEFAULT_SWAP


def cp(mon, level, iv_atk=15, iv_def=15, iv_sta=15):
    """計算 CP:floor((Atk+IV)·√(Def+IV)·√(Sta+IV)·CPM²/10),下限 10。"""
    m = cpm(level)
    raw = ((mon["base"]["atk"] + iv_atk)
           * (mon["base"]["def"] + iv_def) ** 0.5
           * (mon["base"]["sta"] + iv_sta) ** 0.5
           * m * m / 10.0)
    return max(10, floor(raw))


def effective_stats(mon, level, is_shadow):
    """回傳(有效攻擊, 有效防禦, 有效HP)。"""
    m = cpm(level)
    atk = (mon["base"]["atk"] + IV) * m
    dfn = (mon["base"]["def"] + IV) * m
    hp = floor((mon["base"]["sta"] + IV) * m)
    if is_shadow:
        atk *= SHADOW_ATK_MULT
        dfn *= SHADOW_DEF_MULT
    return atk, dfn, hp


def _move_damage(move, atk, mon_types, s, boost_type):
    """單次招式傷害。

    屬性倍率二擇一:
    - s.boss_types 已設定 → 依招式屬性對頭目屬性查真實相剋表(大小招分別計算)
    - 否則 → boost_type(分屬性榜)招式套固定效果絕佳倍率,其餘 1.0
    """
    stab = s.stab if move["type"] in mon_types else 1.0
    if s.boss_types:
        eff = effectiveness(move["type"], s.boss_types)
    else:
        eff = s.type_se_mult if (boost_type and move["type"] == boost_type) else 1.0
    weather = s.weather_mult if s.weather else 1.0
    return s.dmg_coeff * move["power"] * (atk / s.def_boss) * stab * eff * weather + s.dmg_bonus


def _party_boost(party_size, f_to_c_ratio):
    """Party Power:依 fast→charge 循環比例對充能招加成,上限 +100%。"""
    if party_size <= 1:
        return 0.0
    per = {2: 18, 3: 9, 4: 6}.get(party_size, 18)
    return max(0.0, min(f_to_c_ratio / per, 1.0))


def evaluate(mon, fast, charge, s: Settings, boost_type=None):
    """計算某隻寶可夢在指定(快招, 充能招)下的完整指標。

    boost_type:分屬性榜時傳入該屬性,對該屬性招式套效果絕佳倍率(單一弱點模型)。
    回傳 dict:dps / tdo / edps / faints / ttw / hp。
    """
    atk, dfn, hp = effective_stats(mon, s.level, mon["is_shadow"])
    atk *= FRIENDSHIP.get(s.friendship, 1.0)
    atk *= MEGA_BOOST.get(s.mega_boost, 1.0)

    def dur(ms):
        """招式時長(秒);pve_turns 時取整到 0.5s(GO 回合制)。"""
        sec = ms / 1000.0
        return int(sec * 2 + 0.5) / 2 if s.pve_turns else sec

    fdur = dur(fast["duration"])
    cdur = dur(charge["duration"])
    fe = fast["energy"]
    ce = abs(charge["energy"])
    if fdur <= 0 or cdur <= 0 or (fe + ce) <= 0:
        return {"dps": 0.0, "tdo": 0.0, "edps": 0.0, "faints": 0.0, "ttw": 0.0, "hp": hp}

    fdmg = _move_damage(fast, atk, mon["types"], s, boost_type)
    cdmg = _move_damage(charge, atk, mon["types"], s, boost_type)

    y = s.incoming_const / dfn      # 每秒受到的傷害

    fdps = fdmg / fdur
    cdps = cdmg / cdur
    feps = fe / fdur
    ceps = ce / cdur
    # 一格充能招懲罰:陣亡時浪費較多能量 → 有效能量成本上升
    if s.one_bar_penalty and charge["energy"] == -100:
        dws = 0.0 if s.pve_turns else charge.get("dws", 0) / 1000.0
        ceps = (ce + 0.5 * fe + 0.5 * y * dws) / cdur

    x = 0.5 * ce + 0.5 * fe         # 預期殘餘能量
    # 陣亡能量浪費:被首領充能招打死時,受傷累積的能量隨之損失(懲罰脆皮)
    if s.death_energy_waste:
        x += 0.5 * (s.boss_cm_power / dfn)

    # Party Power:估算 fast→charge 循環比例,對充能招 DPS 加成
    if s.party_size > 1:
        tof = hp / y
        denom = (tof * fe - fdur * (x - 0.5 * hp))
        ratio = (tof * ce + cdur * (x - 0.5 * hp)) / denom if denom else 0.0
        cdps *= (1 + _party_boost(s.party_size, ratio))

    dps0 = (fdps * ceps + cdps * feps) / (ceps + feps)
    dps = dps0 + (cdps - fdps) / (ceps + feps) * (0.5 - x / hp) * y
    dps = max(dps, fdps if fdps > 0 else 0.0, 0.0)

    tdo = (hp / y) * dps

    # eDPS:計入陣亡成本 = 換手延遲 +(全隊滅團的重進以隊伍人數攤提)
    per_death = s.swap_time + s.relobby / max(1, s.team_size)
    denom = tdo + dps * per_death
    edps = dps * tdo / denom if denom > 0 else 0.0

    faints = max(0.0, s.boss_hp / tdo) if tdo > 0 else 0.0
    ttw = s.boss_hp / dps if dps > 0 else float("inf")
    return {"dps": dps, "tdo": tdo, "edps": edps, "faints": faints, "ttw": ttw, "hp": hp}


def assign_tier(value, top_value, method, is_type_page, type_se_mult=DEFAULT_TYPE_SE):
    """指派 Tier。

    absolute 法(預設):依固定 eDPS 門檻;分屬性榜先 ÷效果絕佳倍率,把該頁 eDPS
        映回「全域中性尺度」,使各頁 tier 可比(火系頂端不會全變 SSSSS)。
    ratio 法:依 value/top_value 比例,榜首必為最高階。
    """
    if method == "absolute":
        v = value / type_se_mult if (is_type_page and type_se_mult) else value
        for cut, tier in TIER_ABS:
            if v >= cut:
                return tier
        return "C"
    # ratio
    if top_value <= 0:
        return "B"
    r = value / top_value
    for cut, tier in TIER_RATIO:
        if r >= cut:
            return tier
    return "B"
