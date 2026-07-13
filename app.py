"""Streamlit 首頁。啟動:streamlit run app.py"""

import streamlit as st

from i18n import T
from pokecalc import loader
import ui_common

st.set_page_config(page_title=T["app_title"], page_icon="⚔️", layout="wide")

st.title("⚔️ " + T["app_title"])
st.caption(T["app_subtitle"])

if not ui_common.data_available():
    st.error(T["no_data"])
    st.stop()

meta = loader.meta()
pokemon = loader.pokemon()

c1, c2, c3 = st.columns(3)
c1.metric(T["data_version"], str(meta.get("gm_version", "—")))
c2.metric("寶可夢條目數", f"{len(pokemon):,}")
c3.metric(T["built_at"], str(meta.get("built_at", "—"))[:10])

st.divider()
st.markdown(
    f"""
### 使用說明
- 左側可切換到 **{T['nav_attackers']}** 與 **{T['nav_pokedex']}**。
- **{T['nav_attackers']}**:依屬性或整體排名,列出每隻寶可夢最佳招式組合的
  DPS / TDO / **eDPS**;可用側邊欄調整等級、天氣、親密度等設定。
- **{T['nav_pokedex']}**:搜尋任一寶可夢,檢視其數值與各招式組合表現。
- 資料來源為公開的 **PokeMiners GameMaster**,已打包為本地快照,可離線使用。
  需更新時執行:`python scripts/build_data.py`。

> {T['metric_note']}
"""
)
