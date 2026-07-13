"""寶可夢圖鑑頁:搜尋、篩選,並以 dittobase 風格呈現單隻寶可夢的完整資料。

區塊:基本資訊(含實裝狀態切換)、基礎數值(百分位)、CP 一覽、屬性相剋、
天氣加成、攻擊手榜排名、招式表(一般/特殊/組合)。
名字/屬性/招式的視覺與最佳攻擊手頁共用 ui_common 的 HTML helpers。
"""

import bisect
import html as _html

import streamlit as st

from i18n import T, TYPE_COLORS, TYPE_WEATHER, type_zh, types_zh
from pokecalc import calc, loader
from pokecalc.typechart import TYPES, defense_profile
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

st.markdown(ui_common.PGX_CSS, unsafe_allow_html=True)

# --- 深連結:從排名頁點名字帶 ?uid= 進來,消費一次後移除 ---
qp_uid = st.query_params.get("uid")
if qp_uid:
    if any(m["uid"] == qp_uid for m in mons):
        st.session_state["dex_query"] = ""
        st.session_state["dex_types"] = []
        st.session_state["dex_sel"] = qp_uid
    del st.query_params["uid"]

# --- 搜尋與篩選 ---
c1, c2 = st.columns([2, 2])
query = c1.text_input(T["search"], key="dex_query").strip().lower()
sel_types = c2.multiselect(T["filter_types"], TYPES, format_func=type_zh, key="dex_types")


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
labels = {
    m["uid"]: f"#{m['dex']:04d} {loader.zh_pokemon(m)}（{types_zh(m['types'])}）"
              + ("" if m["released"] else T["unreleased_suffix"])
    for m in candidates
}
if st.session_state.get("dex_sel") not in labels:  # 篩選變更後選擇失效 → 重設
    st.session_state.pop("dex_sel", None)
sel_uid = st.selectbox(
    f"{T['nav_pokedex']}（{len(candidates)}）",
    [m["uid"] for m in candidates],
    format_func=lambda u: labels[u],
    key="dex_sel",
)

mon = next(m for m in candidates if m["uid"] == sel_uid)

# ---------------------------------------------------------------- 基本資訊
img_col, info_col = st.columns([1, 3])
with img_col:
    st.image(loader.sprite_url(mon), width="stretch")
with info_col:
    rel = mon["released"]
    rel_badge = (f'<span style="background:{"#22C55E" if rel else "#94A3B8"};color:#fff;'
                 f'border-radius:6px;padding:1px 10px;font-size:.5em;font-weight:700;'
                 f'vertical-align:6px">{T["released_yes" if rel else "released_no"]}</span>')
    st.markdown(
        f'<h2 style="margin-bottom:0">{ui_common.styled_name(loader.zh_pokemon(mon))}'
        f'　<span style="opacity:.6;font-size:.7em">{_html.escape(mon["name_en"])}</span>　{rel_badge}</h2>'
        f'<div style="margin:6px 0 2px"><span style="opacity:.6">#{mon["dex"]:04d}</span>'
        f'　{ui_common.type_cell(mon["types"], sep="　")}</div>',
        unsafe_allow_html=True,
    )

    rel_key = f"rel_{mon['uid']}"

    def _apply_release(uid=mon["uid"], k=rel_key):
        loader.set_released_override(uid, st.session_state[k])

    st.toggle(T["released_toggle"], value=rel, key=rel_key,
              help=T["released_toggle_help"], on_change=_apply_release)

# ---------------------------------------------------------------- 基礎數值 + CP
stat_col, cp_col = st.columns([3, 2])

with stat_col:
    st.subheader(T["base_stats"])
    all_stats = {k: sorted(m["base"][k] for m in mons) for k in ("atk", "def", "sta")}
    eff_atk, eff_def, eff_hp = calc.effective_stats(mon, s.level, mon["is_shadow"])
    bars = []
    for key, label, color, eff in (
        ("atk", T["stat_atk"], "#EF4444", f"{eff_atk:.1f}"),
        ("def", T["stat_def"], "#3B82F6", f"{eff_def:.1f}"),
        ("sta", T["stat_sta"], "#22C55E", f"HP {eff_hp}"),
    ):
        v = mon["base"][key]
        vals = all_stats[key]
        pct = 100.0 * bisect.bisect_left(vals, v) / len(vals)
        width = 100.0 * v / vals[-1]
        bars.append(
            f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0">'
            f'<span style="width:4.2em;opacity:.85">{label}</span>'
            f'<span style="flex:1;background:rgba(128,128,128,.15);border-radius:5px;height:13px;overflow:hidden">'
            f'<span style="display:block;height:100%;width:{width:.1f}%;background:{color};border-radius:5px"></span></span>'
            f'<b style="width:2.6em;text-align:right">{v}</b>'
            f'<span style="opacity:.6;font-size:.85em;width:11em">'
            f'{T["beats_pct"].format(pct=f"{pct:.0f}")}・{eff}</span></div>'
        )
    st.markdown("".join(bars), unsafe_allow_html=True)
    st.caption(T["effective_at_level"].format(level=s.level))

with cp_col:
    st.subheader(T["sec_cp"])
    m1, m2 = st.columns(2)
    m1.metric(T["cp_max40"], f"{calc.cp(mon, 40):,}")
    m2.metric(T["cp_max50"], f"{calc.cp(mon, 50):,}")
    m3, m4 = st.columns(2)
    m3.metric(T["cp_raid"], f"{calc.cp(mon, 20, 10, 10, 10):,}–{calc.cp(mon, 20):,}")
    m4.metric(T["cp_raid_wb"], f"{calc.cp(mon, 25, 10, 10, 10):,}–{calc.cp(mon, 25):,}")
    st.caption(T["cp_iv_note"])

# ---------------------------------------------------------------- 屬性相剋 + 天氣
mu_col, wx_col = st.columns([3, 2])


def _matchup_rows(groups, badge_bg):
    rows = []
    for mult, ts in groups:
        rows.append(
            f'<div style="margin:5px 0"><span style="background:{badge_bg};color:#fff;'
            f'border-radius:5px;padding:1px 7px;font-size:.82em;font-weight:700;'
            f'font-variant-numeric:tabular-nums">×{mult:.2f}</span>　'
            f'{ui_common.type_cell(ts, sep="　")}</div>'
        )
    return "".join(rows) or '<span style="opacity:.5">—</span>'


with mu_col:
    st.subheader(T["sec_matchups"])
    prof = defense_profile(mon["types"])
    weak = [(m, ts) for m, ts in prof.items() if m > 1]
    resist = [(m, ts) for m, ts in prof.items() if m < 1]
    w_col, r_col = st.columns(2)
    w_col.markdown(f"**{T['weaknesses']}**", unsafe_allow_html=True)
    w_col.markdown(_matchup_rows(weak, "#DC2626"), unsafe_allow_html=True)
    r_col.markdown(f"**{T['resistances']}**", unsafe_allow_html=True)
    r_col.markdown(_matchup_rows(resist, "#16A34A"), unsafe_allow_html=True)

_WEATHER_EMOJI = {"晴天": "☀️", "雨天": "🌧️", "下雪": "❄️", "多雲": "☁️",
                  "起霧": "🌫️", "強風": "💨", "時晴": "⛅"}
with wx_col:
    st.subheader(T["sec_weather"])
    lines = []
    for t in mon["types"]:
        w = TYPE_WEATHER[t]
        lines.append(f'<div style="margin:5px 0">{ui_common.type_cell([t], sep="")}'
                     f'　→　{_WEATHER_EMOJI.get(w, "")} <b>{w}</b></div>')
    st.markdown("".join(lines), unsafe_allow_html=True)
    st.caption(T["weather_note"])

# ---------------------------------------------------------------- 攻擊手榜排名
st.subheader(T["sec_rank"])
boards = [(T["rank_overall"], None)] + [(type_zh(t) + T["type_board"], t) for t in mon["types"]]
rank_rows = []
for label, mt in boards:
    df = ui_common.ranking_for(s, move_type=mt)
    hit = df[df["uid"] == mon["uid"]] if not df.empty else df
    if hit.empty:
        reason = T["not_ranked_unreleased"] if (not mon["released"] and not s.include_unreleased) \
            else T["not_ranked"]
        rank_rows.append(f'<tr><td><b>{label}</b></td>'
                         f'<td colspan="4" style="opacity:.55">{reason}</td></tr>')
    else:
        r = hit.iloc[0]
        rank_rows.append(
            f'<tr><td><b>{label}</b></td>'
            f'<td class="pgx-num">#{r["rank"]} / {len(df)}</td>'
            f'<td>{ui_common.tier_chip(r["tier"])}</td>'
            f'<td>{ui_common.move_cell(r["fast"], "", r["fast_type"], ui_common.legacy_badge() if r["fast_elite"] else "")} ・ '
            f'{ui_common.move_cell(r["charge"], "", r["charge_type"], ui_common.legacy_badge() if r["charge_elite"] else "")}</td>'
            f'<td class="pgx-num"><b>{r["edps"]:.2f}</b></td></tr>'
        )
st.markdown(
    f'<div style="overflow-x:auto"><table class="pgx-table"><thead><tr>'
    f'<th></th><th>{T["col_rank"]}</th><th>{T["col_tier"]}</th>'
    f'<th>{T["col_fast"]}／{T["col_charge"]}</th><th>eDPS</th>'
    f'</tr></thead><tbody>{"".join(rank_rows)}</tbody></table></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- 招式表


def _move_label(mid, mv):
    badge = ""
    if mid in mon.get("elite_fast", []) or mid in mon.get("elite_charged", []):
        badge += ui_common.legacy_badge()
    if mv["type"] in mon["types"]:
        badge += ui_common.stab_badge()
    return ui_common.move_cell(loader.zh_move(mid), loader.en_move(mid), mv["type"], badge)


def _moves_table(head, body_rows):
    thead = "".join(f"<th>{h}</th>" for h in head)
    return (f'<div style="overflow-x:auto"><table class="pgx-table">'
            f'<thead><tr>{thead}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>')


fast_all = sorted(set(mon["fast"] + mon.get("elite_fast", [])))
charge_all = sorted(set(mon["charged"] + mon.get("elite_charged", [])))

fm_col, cm_col = st.columns(2)
with fm_col:
    st.subheader(T["fast_moves"])
    rows = []
    for mid in fast_all:
        mv = moves.get(mid)
        if not mv:
            continue
        dur = mv["duration"] / 1000.0
        dps = mv["power"] / dur if dur else 0.0
        eps = mv["energy"] / dur if dur else 0.0
        rows.append(f'<tr><td>{_move_label(mid, mv)}</td>'
                    f'<td class="pgx-num">{mv["power"]:.0f}</td>'
                    f'<td class="pgx-num">{mv["energy"]}</td>'
                    f'<td class="pgx-num">{dur:.1f}s</td>'
                    f'<td class="pgx-num">{dps:.1f}</td>'
                    f'<td class="pgx-num">{eps:.1f}</td></tr>')
    st.markdown(_moves_table(
        [T["col_move"], T["col_power"], T["col_energy"], T["col_duration"], "DPS", "EPS"], rows),
        unsafe_allow_html=True)

with cm_col:
    st.subheader(T["charge_moves"])
    rows = []
    for mid in charge_all:
        mv = moves.get(mid)
        if not mv:
            continue
        dur = mv["duration"] / 1000.0
        energy = abs(mv["energy"])
        n_bars = round(100 / energy) if energy else 0
        dpe = mv["power"] / energy if energy else 0.0
        rows.append(f'<tr><td>{_move_label(mid, mv)}</td>'
                    f'<td class="pgx-num">{mv["power"]:.0f}</td>'
                    f'<td class="pgx-num">{energy}</td>'
                    f'<td style="color:#F59E0B;letter-spacing:2px">{"●" * n_bars}</td>'
                    f'<td class="pgx-num">{dur:.1f}s</td>'
                    f'<td class="pgx-num">{dpe:.2f}</td></tr>')
    st.markdown(_moves_table(
        [T["col_move"], T["col_power"], T["col_energy"], T["col_bars"], T["col_duration"], "DPE"], rows),
        unsafe_allow_html=True)

# ---------------------------------------------------------------- 招式組合表現
st.subheader(T["movesets"])
fast_ids = sorted(set(mon["fast"] + (mon.get("elite_fast", []) if s.include_legacy else [])))
charge_ids = sorted(set(mon["charged"] + (mon.get("elite_charged", []) if s.include_legacy else [])))

combos = []
for fid in fast_ids:
    fm = moves.get(fid)
    if not fm:
        continue
    for cid in charge_ids:
        cm = moves.get(cid)
        if not cm:
            continue
        r = calc.evaluate(mon, fm, cm, s)
        combos.append((fid, fm, cid, cm, r))
combos.sort(key=lambda c: c[4]["edps"], reverse=True)

rows = []
for i, (fid, fm, cid, cm, r) in enumerate(combos):
    best = (f'<span style="background:#22C55E;color:#fff;border-radius:5px;padding:0 6px;'
            f'font-size:.78em;font-weight:700">{T["best_combo"]}</span>') if i == 0 else ""
    rows.append(f'<tr{" class=pgx-best" if i == 0 else ""}>'
                f'<td>{best}</td>'
                f'<td>{_move_label(fid, fm)}</td>'
                f'<td>{_move_label(cid, cm)}</td>'
                f'<td class="pgx-num">{r["dps"]:.2f}</td>'
                f'<td class="pgx-num">{r["tdo"]:.1f}</td>'
                f'<td class="pgx-num"><b>{r["edps"]:.2f}</b></td></tr>')
st.markdown(_moves_table(
    ["", T["col_fast"], T["col_charge"], T["col_dps"], T["col_tdo"], T["col_edps"]], rows),
    unsafe_allow_html=True)
st.caption(T["metric_note"])
