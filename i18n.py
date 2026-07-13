"""UI 繁體中文字串,集中管理方便翻譯與修改。

- T:一般介面字串
- TYPE_ZH:18 種屬性的繁中名稱
"""

T = {
    "app_title": "寶可夢 GO 資料庫",
    "app_subtitle": "最佳攻擊手排名與圖鑑(繁體中文・可離線)",
    "nav_attackers": "最佳攻擊手",
    "nav_pokedex": "寶可夢圖鑑",

    # 設定面板
    "settings": "設定",
    "level": "寶可夢等級",
    "weather": "天氣加成",
    "weather_help": "假設對該攻擊手有利的天氣,套用 1.2 倍",
    "friendship": "親密度加成",
    "rejoin": "重進秒數",
    "rejoin_help": "陣亡後重新加入戰鬥所需秒數,影響 eDPS 與擊敗時間",
    "include_mega": "納入超級/原始進化",
    "include_shadow": "納入暗影寶可夢",
    "include_legacy": "納入傳承/菁英招式",
    "include_unreleased": "納入未實裝寶可夢",
    "include_unreleased_help": "遊戲內尚未開放的寶可夢/形態(如未實裝的達摩形態);預設排除",
    "movesets_per": "每隻顯示招式組數",
    "movesets_per_help": "同一隻寶可夢最多列出幾組招式組合",
    "allow_mixed": "允許混屬性招式組",
    "allow_mixed_help": "分屬性榜:是否允許快招與榜屬性不同(如火系榜的精神利刃超夢);關閉則快招也須同屬性",
    "require_type": "僅限本屬性寶可夢",
    "require_type_help": "分屬性榜只列本身具有該屬性的寶可夢(STAB 必有);關閉即 dittobase 行為(依招式屬性入榜)",

    # 頭目屬性
    "boss_panel": "設定頭目屬性",
    "boss_on": "啟用",
    "boss_on_help": "啟用後不再用固定的效果絕佳倍率,改依快招/充能招各自屬性對頭目查真實相剋表(1.6/0.625/0.39,雙屬性相乘)",
    "boss_t1": "頭目主屬性",
    "boss_t1_limit_help": "分屬性榜下,主屬性僅能選被該榜屬性剋制的屬性",
    "boss_t2": "頭目次屬性",
    "type_none": "無",
    "vs_boss": "vs 頭目",
    "se_not_used": "(頭目屬性啟用時,此固定倍率不適用)",
    "party_power": "隊伍加成(Party Power)",
    "party_power_help": "多人團體戰的充能招加成;1=關閉(單人)",
    "mega_boost": "盟友 Mega 加成",
    "mega_boost_help": "隊友的 Mega 對你的攻擊加成(同屬性 1.3、異屬性 1.1)",
    "team_size": "隊伍人數",
    "team_size_help": "計算 eDPS 時,陣亡重進成本以隊伍人數攤提",
    "tier_method": "Tier 分級方式",
    "tier_method_help": "absolute=固定門檻(全域尺度,分屬性頁會映回全域);ratio=依榜首比例",
    "def_boss": "首領防禦值",
    "def_boss_help": "計算傷害時假設的目標防禦;數值越低傷害越高",
    "incoming": "受擊常數",
    "incoming_help": "每秒受到傷害 = 受擊常數 / 自身防禦;影響 TDO 與存活時間",
    "advanced": "進階校正參數",
    "mb_none": "關閉", "mb_diff": "異屬性(1.1)", "mb_same": "同屬性(1.3)",

    # 公式與參數
    "formula_panel": "計算公式與參數(可即時調整)",
    "formula_intro": "以下公式的常數可即時調整,調整後整張排名表會重新計算。",
    "p_stab": "本系加成 STAB",
    "p_weather": "天氣倍率",
    "p_type_se": "效果絕佳倍率(分屬性)",
    "p_dmg_coeff": "傷害係數",
    "p_dmg_bonus": "傷害加成常數",
    "p_boss_hp": "首領總 HP",
    "p_relobby": "重進秒數",
    "p_swap": "換手秒數",
    "p_swap_help": "每次陣亡換下一隻上場的延遲;重進秒數只在全隊滅團時以隊伍人數攤提",
    "p_boss_cm": "首領充能威力常數",
    "p_boss_cm_help": "陣亡能量浪費項:x += 0.5×(常數/防禦);懲罰脆皮攻擊手",
    "pve_turns": "回合取整(0.5s)",
    "one_bar_penalty": "一格招懲罰",
    "death_energy_waste": "陣亡能量浪費",
    "align_hint": "對齊 dittobase 分屬性榜:效果絕佳倍率 1.98、受擊常數 1745(重進維持 10)",
    "reset_params": "重設為預設值",
    "reset_done": "已重設為預設常數。",

    # 親密度選項
    "fr_none": "無", "fr_good": "好朋友", "fr_great": "好友",
    "fr_ultra": "摯友", "fr_best": "最佳好友",

    # 攻擊手頁
    "attackers_title": "最佳攻擊手排名",
    "select_type": "屬性",
    "type_overall": "整體",
    "topn": "顯示筆數",
    "col_rank": "排名",
    "col_tier": "評級",
    "col_name": "寶可夢",
    "col_types": "屬性",
    "col_fast": "一般招式",
    "col_charge": "特殊招式",
    "col_dps": "DPS",
    "col_tdo": "TDO",
    "col_edps": "eDPS",
    "col_faints": "陣亡次數",
    "col_ttw": "擊敗時間(秒)",
    "metric_note": "eDPS(有效 DPS)為主要排序指標:綜合輸出與存活,並計入陣亡重進的時間損失。",
    "sort_by": "排序依據",
    "sort_desc": "遞減",

    # 圖鑑頁
    "pokedex_title": "寶可夢圖鑑",
    "search": "搜尋寶可夢(繁中名或英文)",
    "filter_types": "篩選屬性",
    "no_result": "找不到符合的寶可夢。",
    "base_stats": "基礎數值",
    "stat_atk": "攻擊", "stat_def": "防禦", "stat_sta": "耐力",
    "movesets": "招式組合表現(依目前設定)",
    "fast_moves": "一般招式",
    "charge_moves": "特殊招式",

    # 其他
    "data_version": "資料版本",
    "built_at": "產出時間",
    "no_data": "找不到資料快照,請先執行:python scripts/build_data.py",
    "select_pokemon": "請從上方選擇一隻寶可夢。",
}

TYPE_ZH = {
    "NORMAL": "一般", "FIRE": "火", "WATER": "水", "ELECTRIC": "電",
    "GRASS": "草", "ICE": "冰", "FIGHTING": "格鬥", "POISON": "毒",
    "GROUND": "地面", "FLYING": "飛行", "PSYCHIC": "超能力", "BUG": "蟲",
    "ROCK": "岩石", "GHOST": "幽靈", "DRAGON": "龍", "DARK": "惡",
    "STEEL": "鋼", "FAIRY": "妖精",
}

# 特定形態的完整繁中名稱覆寫(優先於逐段形態翻譯;key = 寶可夢 uid,不含 _SHADOW)
POKEMON_NAME_OVERRIDES = {
    "NECROZMA_DUSK_MANE": "奈克洛茲瑪(黃昏之鬃)",
    "NECROZMA_DAWN_WINGS": "奈克洛茲瑪(拂曉之翼)",
    "KYUREM_BLACK": "闇黑酋雷姆",
    "KYUREM_WHITE": "焰白酋雷姆",
    "DARMANITAN_GALARIAN_ZEN": "伽勒爾達摩狒狒(達摩模式)",
    "DARMANITAN_ZEN": "達摩狒狒(達摩模式)",
}

# 18 屬性代表色(官方風格,用於卡片/徽章)
TYPE_COLORS = {
    "NORMAL": "#9099A1", "FIRE": "#FF9C54", "WATER": "#4D90D5", "ELECTRIC": "#F3D23B",
    "GRASS": "#63BB5B", "ICE": "#74CEC0", "FIGHTING": "#CE4069", "POISON": "#AB6AC8",
    "GROUND": "#D97746", "FLYING": "#8FA8DD", "PSYCHIC": "#F97176", "BUG": "#90C12C",
    "ROCK": "#C7B78B", "GHOST": "#5269AC", "DRAGON": "#0A6DC4", "DARK": "#5A5366",
    "STEEL": "#5A8EA1", "FAIRY": "#EC8FE6",
}

# Tier 徽章色
TIER_COLORS = {
    "SSSSS": "#E4407A", "SSSS": "#F0663F", "SSS": "#F59E0B", "SS": "#84CC16",
    "S": "#22C55E", "A": "#38BDF8", "B": "#94A3B8", "C": "#CBD5E1",
    "D": "#E2E8F0", "F": "#E2E8F0",
}


def type_zh(t):
    return TYPE_ZH.get(t, t)


def types_zh(types):
    return "／".join(type_zh(t) for t in types)
