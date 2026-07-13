# PokeGoDex — 寶可夢 GO 最佳攻擊手排名與圖鑑(繁體中文)

以公開的 **PokeMiners GameMaster** 資料,套用標準的 Pokémon GO 傷害公式,
計算每隻寶可夢的 **DPS / TDO / eDPS**,並依屬性與整體排名呈現。
功能對標 [dittobase best-attackers](https://www.dittobase.com/pokemon-go/best-attackers),
但完全在地端執行、介面繁體中文、純 Python 可自由修改。

## 快速開始

```bash
# 1. 安裝依賴
python3 -m pip install -r requirements.txt

# 2.(選用)更新資料快照 —— 需連網,會下載最新 GameMaster
python3 scripts/build_data.py

# 3. 啟動網頁介面
python3 -m streamlit run app.py
```

> 若 `streamlit` 指令不在 PATH,請改用 `python3 -m streamlit run app.py`。
> 啟動後瀏覽器開啟終端機顯示的 Local URL(預設 http://localhost:8501)。

`data/` 已內含打包好的快照,**未連網也能直接執行第 3 步**。

## 頁面

- **最佳攻擊手**:依屬性(18 種)或整體排名,列出每隻寶可夢最佳招式組合的
  DPS / TDO / eDPS / 陣亡次數 / 擊敗時間;可用側邊欄調整設定。
- **寶可夢圖鑑**:搜尋/篩選任一寶可夢,檢視數值與各招式組合表現。

側邊欄設定:等級、天氣加成、親密度、隊伍加成(Party Power)、盟友 Mega 加成、
隊伍人數、Tier 分級方式,以及是否納入 超級進化 / 暗影 / 傳承招式 / **未實裝寶可夢**、
**允許混屬性招式組**、**每隻顯示招式組數(1–3)**。

排名頁頂部有 dittobase 風格的 **Top 4 卡片區**(Pokémon GO 官方風格圖示、屬性色、
Tier 徽章);名稱與招式均**中英並存**(如「噴火龍 Charizard」「火焰旋渦 Fire Spin」)。

**🎯 設定頭目屬性**(排名頁/圖鑑頁控制列):啟用後不再用固定效果絕佳倍率,
改依快招/充能招**各自屬性**對頭目主/次屬性查真實相剋表(1.6/0.625/0.39,雙屬性相乘),
即「對策查詢」模式 —— 例:頭目=龍/飛 → 冰招 ×2.56,焰白酋雷姆登頂。
分屬性榜下,頭目主屬性僅能選被該榜屬性剋制者;側邊欄另有「僅限本屬性寶可夢」
開關(預設開,保證 STAB;關閉即 dittobase 行為)。

表格頂端的「🧮 計算公式與參數」面板會用數學式展示 DPS / TDO / eDPS 公式,
並可**即時調整公式中的常數**(首領防禦、受擊常數、STAB、天氣倍率、效果絕佳倍率、
傷害係數、首領 HP、重進秒數…),調整後整張排名表立即重算,附「重設為預設值」。

## 專案結構

```
app.py                  Streamlit 首頁
pages/                  多頁(最佳攻擊手、寶可夢圖鑑)
ui_common.py            側邊欄設定面板 + 快取排名
i18n.py                 介面繁中字串 + 屬性名稱(要改字改這裡)
pokecalc/               計算核心(與 UI 分離)
  ├─ calc.py            傷害 / DPS / TDO / eDPS / Tier 公式
  ├─ rankings.py        枚舉招式組合並排序
  ├─ typechart.py       屬性相剋表
  ├─ cpm.py             等級係數表
  └─ loader.py          讀取快照 + 繁中名稱查詢
scripts/build_data.py   下載並產出 data/*.json 快照
data/                   本地資料快照(打包於 repo)
```

## 計算方法(對齊開源標準 DialgaDex;常數可在介面或 `pokecalc/calc.py` 調整)

- 傷害/次 = `0.5 × 威力 × (攻擊/首領防禦) × STAB × 屬性倍率 × 天氣 + 0.5`
- 綜合 DPS 採 GamePress「Comprehensive DPS」公式(計入能量循環、Party Power)
- **eDPS**(主要排序指標)= 有效長期 DPS,計入陣亡重進(以隊伍人數攤提):
  `eDPS = DPS × TDO / (TDO + DPS × 重進/隊伍人數)`
- 預設常數:首領防禦 `180`、受擊常數 `1970`、首領 HP `15000`(Faints=HP/TDO、TTW=HP/DPS)
- **分屬性榜**對「該屬性弱點的首領」計算,套 `1.6` 倍效果絕佳(火系等數值因而較整體榜高)
- **Tier**:以全域尺度 eDPS 對固定門檻分級(SSSSS→C);分屬性頁先 ÷1.6 映回全域,
  故各頁 tier 可比(如火系頂端為 SSS,與參考網站一致)

- 進階公式細節(預設開啟,對齊 DialgaDex `newdps`):回合取整(0.5s)、一格招懲罰、
  **陣亡能量浪費**(`x += 0.5×(首領充能威力常數/防禦)`,懲罰脆皮攻擊手)

> **對齊 dittobase**:dittobase 分屬性榜以「當期實際首領池」平均計算;在公式面板將
> **效果絕佳倍率 1.98、受擊常數 1745**(重進秒數維持 10,與 dittobase 相同)即可將
> 火系榜對齊到誤差 <2%(排名順序一致)。預設值(1.6/1970)則為理論「單一弱點」模型。
> eDPS 的每次陣亡成本 = **換手秒數(預設 0.6)** + 重進秒數/隊伍人數。

## 名稱翻譯

- 寶可夢與招式的繁中名稱來自 PokeMiners 官方繁中文字檔,存於 `data/names_zh_tw.json`。
- 形態標籤(超級 / 暗影 / 阿羅拉…)的翻譯在 `scripts/build_data.py` 的 `FORM_LABEL_ZH`;
  介面字串與屬性名稱在 `i18n.py`。

## 已知限制

- 資料以打包當下的 GameMaster 為準;若某些超級進化(如 Mega Mewtwo)尚未寫入
  該版 GameMaster,重跑 `build_data.py` 取得最新版即會納入。
- GameMaster 會將部分尚未實裝的暗影寶可夢一併標記,排名可能出現現實中無法取得的暗影傳說;
  可用側邊欄「納入暗影寶可夢」關閉,或自行在資料層過濾。
- 數值為模型估算,絕對值可用進階參數(首領防禦值、受擊常數)校正到與其他網站一致。

## 資料來源與授權

- 遊戲資料:[PokeMiners/game_masters](https://github.com/PokeMiners/game_masters)、
  繁中文字:[PokeMiners/pogo_assets](https://github.com/PokeMiners/pogo_assets)
- released/暗影旗標與 GO 風格圖示:[mgrann03/pokemon-resources](https://github.com/mgrann03/pokemon-resources)
- 下載已內建**多鏡像輪替與重試退避**(raw.githubusercontent → jsDelivr → GitHub API),
  避免 429 限流;更新失敗時自動保留舊快照。
- 本專案為自建程式碼,未複製 dittobase 或其他專案的原始碼。
