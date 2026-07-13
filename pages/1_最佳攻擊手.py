"""最佳攻擊手排名頁(對應 dittobase best-attackers)。

呈現採自製 HTML(卡片區 + 表格合併為單一 st.markdown 元件):
- 單一元件 → 切換屬性/設定時整區原子替換,不會出現圖與名字短暫錯對
- 支援 Tier 合併儲存格(rowspan)、寶可夢圖+中英雙名複合欄、屬性配色與官方小圖標
"""

import html as _html

import streamlit as st

from i18n import T, TIER_COLORS, TYPE_COLORS, type_zh
from pokecalc.typechart import TYPES
import ui_common

st.set_page_config(page_title=T["nav_attackers"], page_icon="⚔️", layout="wide")
st.title("⚔️ " + T["attackers_title"])

if not ui_common.data_available():
    st.error(T["no_data"])
    st.stop()

ui_common.render_sidebar()

# ---------------------------------------------------------------- 控制列
c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
with c1:
    sel_type = st.selectbox(
        T["select_type"], ["ALL"] + TYPES,
        format_func=lambda t: T["type_overall"] if t == "ALL" else type_zh(t),
    )
with c2:
    topn = st.selectbox(T["topn"], [25, 50, 100, 0],
                        format_func=lambda n: "全部" if n == 0 else str(n))
with c3:
    sort_key = st.selectbox(
        T["sort_by"], ["edps", "dps", "tdo", "ttw", "rank"],
        format_func=lambda k: {"edps": "eDPS", "dps": "DPS", "tdo": "TDO",
                               "ttw": T["col_ttw"], "rank": T["col_rank"]}[k],
    )
with c4:
    desc = st.checkbox(T["sort_desc"], value=(sort_key != "rank"))

move_type = None if sel_type == "ALL" else sel_type
ui_common.render_boss_panel(move_type)
ui_common.render_formula_panel()

s = ui_common.build_settings()
df = ui_common.ranking_for(s, move_type=move_type)

if df.empty:
    st.warning(T["no_result"])
    st.stop()

# ---------------------------------------------------------------- HTML 產生器
_TYPE_ICON = "https://cdn.jsdelivr.net/gh/PokeMiners/pogo_assets@master/Images/Types/POKEMON_TYPE_{t}.png"


def type_icon(t, size=16):
    return (f'<img src="{_TYPE_ICON.format(t=t)}" width="{size}" height="{size}" '
            f'style="vertical-align:-3px" loading="lazy">')


def type_cell(types):
    parts = []
    for t in types:
        c = TYPE_COLORS.get(t, "#888")
        parts.append(f'{type_icon(t)}&nbsp;<span style="color:{c};font-weight:600">{type_zh(t)}</span>')
    return "<br>".join(parts)


def move_cell(zh, en, t):
    c = TYPE_COLORS.get(t, "#888")
    return (f'{type_icon(t)}&nbsp;<span style="color:{c};font-weight:600">{_html.escape(zh)}'
            f' <span style="opacity:.6;font-size:.85em;font-weight:400">{_html.escape(en)}</span></span>')


def tier_chip(tier):
    return (f'<span style="background:{TIER_COLORS.get(tier, "#94A3B8")};color:#fff;'
            f'border-radius:6px;padding:1px 8px;font-weight:700;font-size:.85em">{tier}</span>')


def pokemon_cell(r):
    return (f'<div style="display:flex;align-items:center;gap:10px">'
            f'<img src="{r["sprite"]}" width="64" height="64" loading="lazy" '
            f'style="object-fit:contain;flex:none">'
            f'<div><div style="font-weight:700">{ui_common.styled_name(r["name"])}</div>'
            f'<div style="opacity:.6;font-size:.85em">{_html.escape(r["name_en"])}</div></div></div>')


def build_cards(df4, accent, title):
    cards = []
    for _, r in df4.iterrows():
        cards.append(f"""
<div style="flex:1;min-width:170px;border:1px solid rgba(128,128,128,.35);border-radius:12px;
     border-top:5px solid {accent};padding:10px 6px;text-align:center">
  <img src="{r['sprite']}" width="92" height="92" style="object-fit:contain"><br>
  {tier_chip(r['tier'])}
  <div style="font-weight:700;font-size:1.02em;margin-top:2px">#{r['rank']} {ui_common.styled_name(r['name'])}</div>
  <div style="opacity:.6;font-size:.8em">{_html.escape(r['name_en'])}</div>
  <div style="font-size:.82em;margin-top:4px">{move_cell(r['fast'], '', r['fast_type'])} ・ {move_cell(r['charge'], '', r['charge_type'])}</div>
  <div style="font-size:.9em;margin-top:2px"><b>eDPS {r['edps']:.2f}</b>　TDO {r['tdo']:.0f}</div>
</div>""")
    return (f'<h4><span style="background:{accent};color:#fff;border-radius:8px;'
            f'padding:2px 14px">{title}</span>　最強攻擊手 Top 4</h4>'
            f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px">{"".join(cards)}</div>')


def build_table(view, use_rowspan):
    head_cols = [T["col_tier"], T["col_rank"], T["col_name"], T["col_types"],
                 T["col_fast"], T["col_charge"], "DPS", "TDO", "eDPS",
                 T["col_faints"], T["col_ttw"]]
    thead = "".join(f"<th>{h}</th>" for h in head_cols)

    # 同 tier 連續列數(rowspan 用)
    tiers = list(view["tier"])
    runs = {}
    i = 0
    while i < len(tiers):
        j = i
        while j < len(tiers) and tiers[j] == tiers[i]:
            j += 1
        runs[i] = j - i
        i = j

    rows = []
    for pos, (_, r) in enumerate(view.iterrows()):
        tds = []
        if use_rowspan:
            if pos in runs:
                tc = TIER_COLORS.get(r["tier"], "#94A3B8")
                tds.append(f'<td rowspan="{runs[pos]}" class="pgx-tier" '
                           f'style="background:{tc}">{r["tier"]}</td>')
        else:
            tds.append(f"<td>{tier_chip(r['tier'])}</td>")
        tds.append(f'<td class="pgx-num">{r["rank"]}</td>')
        tds.append(f"<td>{pokemon_cell(r)}</td>")
        tds.append(f"<td>{type_cell(r['types'])}</td>")
        tds.append(f"<td>{move_cell(r['fast'], r['fast_en'], r['fast_type'])}</td>")
        tds.append(f"<td>{move_cell(r['charge'], r['charge_en'], r['charge_type'])}</td>")
        tds.append(f'<td class="pgx-num">{r["dps"]:.2f}</td>')
        tds.append(f'<td class="pgx-num">{r["tdo"]:.1f}</td>')
        tds.append(f'<td class="pgx-num"><b>{r["edps"]:.2f}</b></td>')
        tds.append(f'<td class="pgx-num">{r["faints"]:.1f}</td>')
        tds.append(f'<td class="pgx-num">{r["ttw"]:.0f}s</td>')
        rows.append(f"<tr>{''.join(tds)}</tr>")

    return (f'<div style="overflow-x:auto"><table class="pgx-table">'
            f"<thead><tr>{thead}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


_CSS = """
<style>
.pgx-table {width:100%;border-collapse:collapse;font-size:.92em}
.pgx-table th {background:rgba(128,128,128,.14);padding:7px 8px;text-align:left;
  border-bottom:2px solid rgba(128,128,128,.4);white-space:nowrap}
.pgx-table td {padding:6px 8px;border-bottom:1px solid rgba(128,128,128,.22);vertical-align:middle}
.pgx-table tbody tr:hover td {background:rgba(128,128,128,.08)}
.pgx-num {text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.pgx-tier {color:#fff;font-weight:800;text-align:center;min-width:56px;
  border-bottom:1px solid rgba(255,255,255,.35) !important}
</style>
"""

# ---------------------------------------------------------------- 組裝與輸出
view = df.copy()
ascending = not desc
view = view.sort_values(sort_key, ascending=ascending).reset_index(drop=True)
if topn:
    view = view.head(topn)

# Tier 只有在按 eDPS / 排名 排序時是連續區塊,才能合併儲存格
use_rowspan = sort_key in ("edps", "rank")

accent = TYPE_COLORS.get(move_type, "#6366F1")
title = T["type_overall"] if move_type is None else type_zh(move_type)
if s.boss_types:
    title += f"　{T['vs_boss']}({'／'.join(type_zh(t) for t in s.boss_types)})"

html = _CSS + build_cards(df.head(4), accent, title) + build_table(view, use_rowspan)
st.markdown(html, unsafe_allow_html=True)  # 單一元件:卡片+表格一次原子更新

st.caption(T["metric_note"] + f"　共 {len(df)} 筆結果，顯示 {len(view)} 筆。")
