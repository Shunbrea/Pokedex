"""寶可夢圖鑑頁:搜尋、篩選、檢視單隻寶可夢與其招式組合表現。"""

import pandas as pd
import streamlit as st

from i18n import T, type_zh, types_zh
from pokecalc import calc, loader
from pokecalc.typechart import TYPES
import ui_common

st.set_page_config(page_title=T["nav_pokedex"], page_icon="📘", layout="wide")
st.title("📘 " + T["pokedex_title"])

if not ui_common.data_available():
    st.error(T["no_data"])
    st.stop()

ui_common.render_sidebar()
ui_common.render_boss_panel()  # 圖鑑頁:主屬性自由選
ui_common.render_formula_panel()
s = ui_common.build_settings()
mons = loader.pokemon()
moves = loader.moves()

# --- 搜尋與篩選 ---
c1, c2 = st.columns([2, 2])
query = c1.text_input(T["search"], "").strip().lower()
sel_types = c2.multiselect(T["filter_types"], TYPES, format_func=type_zh)


def match(mon):
    if sel_types and not any(t in mon["types"] for t in sel_types):
        return False
    if query:
        name = loader.zh_pokemon(mon).lower()
        if query not in name and query not in mon["name_en"].lower():
            return False
    return True


candidates = [m for m in mons if match(m)]
if not candidates:
    st.warning(T["no_result"])
    st.stop()

candidates.sort(key=lambda m: (m["dex"], m["uid"]))
labels = {m["uid"]: f"#{m['dex']:04d} {loader.zh_pokemon(m)}（{types_zh(m['types'])}）" for m in candidates}
sel_uid = st.selectbox(
    f"{T['nav_pokedex']}（{len(candidates)}）",
    [m["uid"] for m in candidates],
    format_func=lambda u: labels[u],
)

mon = next(m for m in candidates if m["uid"] == sel_uid)

# --- 基本資訊(含圖片) ---
img_col, info_col = st.columns([1, 3])
with img_col:
    st.image(loader.sprite_url(mon), width="stretch")
with info_col:
    st.markdown(
        f'<h2 style="margin-bottom:0">{ui_common.styled_name(loader.zh_pokemon(mon))}'
        f'　<span style="opacity:.6;font-size:.7em">{mon["name_en"]}</span></h2>',
        unsafe_allow_html=True,
    )
    st.caption(f"#{mon['dex']:04d} · {types_zh(mon['types'])}")
    atk, dfn, hp = calc.effective_stats(mon, s.level, mon["is_shadow"])
    b1, b2, b3, b4 = st.columns(4)
    b1.metric(T["stat_atk"], mon["base"]["atk"], f"有效 {atk:.1f}")
    b2.metric(T["stat_def"], mon["base"]["def"], f"有效 {dfn:.1f}")
    b3.metric(T["stat_sta"], mon["base"]["sta"], f"HP {hp}")
    b4.metric("等級", f"L{s.level}")

# --- 招式組合表現 ---
st.subheader(T["movesets"])
fast_ids = sorted(set(mon["fast"] + (mon.get("elite_fast", []) if s.include_legacy else [])))
charge_ids = sorted(set(mon["charged"] + (mon.get("elite_charged", []) if s.include_legacy else [])))

rows = []
for fid in fast_ids:
    fm = moves.get(fid)
    if not fm:
        continue
    for cid in charge_ids:
        cm = moves.get(cid)
        if not cm:
            continue
        r = calc.evaluate(mon, fm, cm, s)
        rows.append({
            T["col_fast"]: f"{loader.zh_move(fid)} {loader.en_move(fid)}（{type_zh(fm['type'])}）",
            T["col_charge"]: f"{loader.zh_move(cid)} {loader.en_move(cid)}（{type_zh(cm['type'])}）",
            T["col_dps"]: r["dps"],
            T["col_tdo"]: r["tdo"],
            T["col_edps"]: r["edps"],
        })

mdf = pd.DataFrame(rows).sort_values(T["col_edps"], ascending=False).reset_index(drop=True)
st.dataframe(
    mdf, width="stretch", hide_index=True,
    column_config={
        T["col_dps"]: st.column_config.NumberColumn(format="%.2f"),
        T["col_tdo"]: st.column_config.NumberColumn(format="%.1f"),
        T["col_edps"]: st.column_config.NumberColumn(format="%.2f"),
    },
)
st.caption(T["metric_note"])
