"""Streamlit 頁面共用:側邊欄設定、公式參數面板、快取排名計算。

所有設定值存於 st.session_state 跨頁共享;calc.Settings 由 session_state 建立。
"""

import html as _html

import streamlit as st

from pokecalc import calc, loader, rankings
from pokecalc.typechart import CHART, TYPES
from i18n import T, type_zh

# 特殊形態關鍵字徽章色:暗影=紫、超級=玫紅、原始=琥珀
_PREFIX_BADGES = [("暗影", "#7C3AED"), ("超級", "#E11D48"), ("原始", "#F59E0B")]


def styled_name(name: str) -> str:
    """寶可夢繁中名 → HTML:開頭的 暗影/超級(X/Y)/原始 轉為彩色徽章。"""
    for kw, color in _PREFIX_BADGES:
        if name.startswith(kw):
            rest = name[len(kw):]
            if kw == "超級" and rest[:1] in ("X", "Y"):  # 超級X / 超級Y 整組入徽章
                kw, rest = kw + rest[:1], rest[1:]
            return (f'<span style="background:{color};color:#fff;border-radius:5px;'
                    f'padding:0 6px;font-size:.78em;font-weight:700;'
                    f'vertical-align:1px">{kw}</span> {_html.escape(rest)}')
    return _html.escape(name)

# 所有可調設定的預設值(key 對應 calc.Settings 欄位)
DEFAULTS = {
    # 遊戲性 filters(側邊欄)
    "level": 40, "weather": False, "friendship": "none",
    "party_size": 1, "mega_boost": "none", "team_size": 6,
    "include_mega": True, "include_shadow": True, "include_legacy": True,
    "include_unreleased": False, "movesets_per_pokemon": 1, "allow_mixed": True,
    "require_type": True,
    "boss_on": False, "boss_type1": "NONE", "boss_type2": "NONE",
    "tier_method": "absolute",
    # 公式常數(公式面板)
    "def_boss": calc.DEFAULT_DEF_BOSS, "incoming_const": calc.DEFAULT_INCOMING,
    "stab": calc.DEFAULT_STAB, "weather_mult": calc.DEFAULT_WEATHER,
    "type_se_mult": calc.DEFAULT_TYPE_SE, "dmg_coeff": calc.DEFAULT_DMG_COEFF,
    "dmg_bonus": calc.DEFAULT_DMG_BONUS, "boss_hp": calc.DEFAULT_BOSS_HP,
    "relobby": calc.DEFAULT_RELOBBY,
    "pve_turns": True, "one_bar_penalty": True, "death_energy_waste": True,
    "boss_cm_power": 11670.0, "swap_time": calc.DEFAULT_SWAP,
}


def _ensure_defaults():
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


def _reset_params():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


def data_available():
    try:
        loader.pokemon()
        return True
    except FileNotFoundError:
        return False


def render_sidebar():
    """側邊欄:遊戲性 filters。"""
    _ensure_defaults()
    sb = st.sidebar
    sb.header("⚙️ " + T["settings"])

    sb.selectbox(T["level"], [40, 50, 51], key="level")
    sb.checkbox(T["weather"], help=T["weather_help"], key="weather")

    fr = {"none": T["fr_none"], "good": T["fr_good"], "great": T["fr_great"],
          "ultra": T["fr_ultra"], "best": T["fr_best"]}
    sb.selectbox(T["friendship"], list(fr), format_func=lambda k: fr[k], key="friendship")

    sb.selectbox(T["party_power"], [1, 2, 3, 4],
                 format_func=lambda n: T["fr_none"] if n == 1 else f"{n} 人",
                 help=T["party_power_help"], key="party_size")

    mb = {"none": T["mb_none"], "diff": T["mb_diff"], "same": T["mb_same"]}
    sb.selectbox(T["mega_boost"], list(mb), format_func=lambda k: mb[k],
                 help=T["mega_boost_help"], key="mega_boost")

    sb.divider()
    sb.checkbox(T["include_mega"], key="include_mega")
    sb.checkbox(T["include_shadow"], key="include_shadow")
    sb.checkbox(T["include_legacy"], key="include_legacy")
    sb.checkbox(T["include_unreleased"], help=T["include_unreleased_help"], key="include_unreleased")
    sb.checkbox(T["allow_mixed"], help=T["allow_mixed_help"], key="allow_mixed")
    sb.checkbox(T["require_type"], help=T["require_type_help"], key="require_type")
    sb.selectbox(T["movesets_per"], [1, 2, 3], help=T["movesets_per_help"], key="movesets_per_pokemon")

    sb.divider()
    tm = {"absolute": "absolute", "ratio": "ratio"}
    sb.selectbox(T["tier_method"], list(tm), help=T["tier_method_help"], key="tier_method")
    sb.slider(T["team_size"], 1, 6, help=T["team_size_help"], key="team_size")


def render_boss_panel(move_type=None):
    """頭目屬性設定面板(放控制列下方)。

    move_type 非 None(分屬性榜)時,主屬性僅能選「被該榜屬性剋制」的屬性。
    結果經 session_state(boss_on / boss_type1 / boss_type2)由 build_settings 組成 tuple。
    """
    _ensure_defaults()
    with st.expander("🎯 " + T["boss_panel"], expanded=bool(st.session_state.get("boss_on"))):
        c0, c1, c2 = st.columns([1, 2, 2])
        c0.checkbox(T["boss_on"], help=T["boss_on_help"], key="boss_on")
        enabled = st.session_state["boss_on"]

        if move_type:
            opts = [t for t in TYPES if CHART[move_type][t] > 1.0]
            help1 = T["boss_t1_limit_help"]
            if not opts:  # 一般系:無效果絕佳目標,主屬性開放全選
                opts = list(TYPES)
                help1 = None
        else:
            opts = list(TYPES)
            help1 = None
        if st.session_state["boss_type1"] not in opts:
            st.session_state["boss_type1"] = opts[0]
        c1.selectbox(T["boss_t1"], opts, format_func=type_zh, help=help1,
                     key="boss_type1", disabled=not enabled)

        opts2 = ["NONE"] + [t for t in TYPES if t != st.session_state["boss_type1"]]
        if st.session_state["boss_type2"] not in opts2:
            st.session_state["boss_type2"] = "NONE"
        c2.selectbox(T["boss_t2"], opts2,
                     format_func=lambda t: T["type_none"] if t == "NONE" else type_zh(t),
                     key="boss_type2", disabled=not enabled)


def boss_types_from_state():
    """由 session_state 取得目前生效的頭目屬性 tuple(未啟用 → 空)。"""
    ss = st.session_state
    if not ss.get("boss_on"):
        return ()
    return tuple(t for t in (ss.get("boss_type1", "NONE"), ss.get("boss_type2", "NONE"))
                 if t and t != "NONE")


def render_formula_panel():
    """主畫面頂端:展示公式並提供常數即時調整。"""
    _ensure_defaults()
    with st.expander("🧮 " + T["formula_panel"], expanded=False):
        st.caption(T["formula_intro"])
        st.latex(r"傷害_{次} = c \cdot 威力 \cdot \frac{攻擊}{首領防禦} \cdot STAB \cdot 屬性倍率 \cdot 天氣 + b")
        st.latex(r"DPS = DPS_0 + \frac{CDPS-FDPS}{CEPS+FEPS}\left(0.5-\frac{x}{HP}\right)y,\quad y=\frac{受擊常數}{防禦}")
        st.latex(r"TDO = \frac{HP}{y}\cdot DPS \qquad eDPS = \frac{DPS\cdot TDO}{TDO + DPS\cdot(換手 + 重進/隊伍)}")

        c1, c2, c3 = st.columns(3)
        c1.number_input(T["def_boss"], 50.0, 400.0, step=5.0, help=T["def_boss_help"], key="def_boss")
        c1.number_input(T["incoming"], 300.0, 4000.0, step=10.0, help=T["incoming_help"], key="incoming_const")
        c1.number_input(T["p_boss_hp"], 1000.0, 60000.0, step=500.0, key="boss_hp")
        c2.number_input(T["p_stab"], 1.0, 2.0, step=0.05, key="stab")
        c2.number_input(T["p_weather"], 1.0, 2.0, step=0.05, key="weather_mult")
        c2.number_input(T["p_type_se"], 1.0, 3.0, step=0.05,
                        help=T["se_not_used"], key="type_se_mult")
        c3.number_input(T["p_dmg_coeff"], 0.1, 1.0, step=0.05, key="dmg_coeff")
        c3.number_input(T["p_dmg_bonus"], 0.0, 2.0, step=0.5, key="dmg_bonus")
        c3.number_input(T["p_relobby"], 0.0, 30.0, step=1.0, key="relobby")
        c3.number_input(T["p_swap"], 0.0, 5.0, step=0.1, help=T["p_swap_help"], key="swap_time")

        t1, t2, t3, t4 = st.columns(4)
        t1.checkbox(T["pve_turns"], key="pve_turns")
        t2.checkbox(T["one_bar_penalty"], key="one_bar_penalty")
        t3.checkbox(T["death_energy_waste"], key="death_energy_waste")
        t4.number_input(T["p_boss_cm"], 0.0, 30000.0, step=500.0,
                        help=T["p_boss_cm_help"], key="boss_cm_power")

        st.caption("💡 " + T["align_hint"])
        st.button("↺ " + T["reset_params"], on_click=_reset_params)


def build_settings() -> calc.Settings:
    """由 session_state 建立 calc.Settings(於側邊欄與公式面板渲染後呼叫)。"""
    _ensure_defaults()
    ss = st.session_state
    return calc.Settings(
        level=ss["level"], weather=ss["weather"], friendship=ss["friendship"],
        party_size=ss["party_size"], mega_boost=ss["mega_boost"],
        include_mega=ss["include_mega"], include_shadow=ss["include_shadow"],
        include_legacy=ss["include_legacy"], include_unreleased=ss["include_unreleased"],
        movesets_per_pokemon=ss["movesets_per_pokemon"], allow_mixed=ss["allow_mixed"],
        require_type=ss["require_type"], boss_types=boss_types_from_state(),
        tier_method=ss["tier_method"],
        def_boss=ss["def_boss"], incoming_const=ss["incoming_const"], boss_hp=ss["boss_hp"],
        stab=ss["stab"], weather_mult=ss["weather_mult"], type_se_mult=ss["type_se_mult"],
        dmg_coeff=ss["dmg_coeff"], dmg_bonus=ss["dmg_bonus"],
        relobby=ss["relobby"], team_size=ss["team_size"],
        pve_turns=ss["pve_turns"], one_bar_penalty=ss["one_bar_penalty"],
        death_energy_waste=ss["death_energy_waste"], boss_cm_power=ss["boss_cm_power"],
        swap_time=ss["swap_time"],
    )


@st.cache_data(show_spinner="計算排名中…")
def _cached_ranking(key, move_type):
    """key 為 Settings 所有欄位的 tuple(快取鍵),move_type 為屬性。"""
    s = calc.Settings(**dict(key))
    return rankings.build_ranking(s, move_type=move_type)


def ranking_for(s: calc.Settings, move_type=None):
    key = tuple(sorted(s.__dict__.items()))
    return _cached_ranking(key, move_type)
