"""build_data.py — 下載 Pokemon GO 公開資料,解析並產出精簡的本地快照到 data/ 目錄。

資料來源:
  - mgrann03/pokemon-resources(寶可夢清單/數值/招式/released/shadow 旗標、GO 風格圖示檔名)
  - PokeMiners 繁中文字檔(名稱)

用法:
    python scripts/build_data.py            # 從網路下載最新資料
    python scripts/build_data.py --local 目錄  # 使用本地既有的三個來源 JSON(離線用)

產出:
    data/pokemon.json      每隻寶可夢(含形態/Mega/Shadow)數值、招式、released、sprite
    data/moves.json        每個招式的威力/能量/時長/屬性
    data/names_zh_tw.json  寶可夢與招式的繁中名稱對照
    data/meta.json         資料版本與產出時間

下載強韌化:多鏡像輪替(raw.githubusercontent → jsDelivr → GitHub API)+ 指數退避重試,
以避免 429 Too Many Requests。
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

# --- 資料來源(owner/repo, branch, path)---
RES_REPO = "mgrann03/pokemon-resources"
SRC_PKM = (RES_REPO, "main", "pogo_pkm.min.json")
SRC_FM = (RES_REPO, "main", "pogo_fm.json")
SRC_CM = (RES_REPO, "main", "pogo_cm.json")
ZH_REPO = ("PokeMiners/pogo_assets", "master", "Texts/Latest%20APK/JSON/i18n_chinesetraditional.json")
RES_TREE_URL = f"https://api.github.com/repos/{RES_REPO}/git/trees/HEAD?recursive=1"
RES_VER_URL = f"https://api.github.com/repos/{RES_REPO}/commits/main"

# 首領限定/不可實際使用的形態(不納入攻擊手排名)
EXCLUDE_FORMS = {"ETERNAMAX"}

# 英文種族名 → GM 風格 pokemon_id 的特例(其餘由通用規則推導)
PID_OVERRIDES = {"Nidoran♀": "NIDORAN_FEMALE", "Nidoran♂": "NIDORAN_MALE"}

# 英文招式名 → GM 風格 move id 的特例(GM 連寫/拆字/舊拼法)
MOVE_ID_OVERRIDES = {
    "Future Sight": "FUTURESIGHT",
    "Pyro Ball": "PYROBALL",
    "Superpower": "SUPER_POWER",
    "Vise Grip": "VICE_GRIP",
}

# 來源 form 值的別名(GM 殘留的重複條目)
FORM_ALIASES = {"Nidoran_normal": "Normal"}

# 形態(form)後綴的繁中對照;找不到時回退英文
FORM_LABEL_ZH = {
    "ALOLA": "阿羅拉", "ALOLAN": "阿羅拉",
    "GALARIAN": "伽勒爾", "HISUIAN": "洗翠", "PALDEA": "帕底亞",
    "MEGA": "超級", "MEGA_X": "超級X", "MEGA_Y": "超級Y", "PRIMAL": "原始",
    "SHADOW": "暗影",
    "ORIGIN": "起源", "ALTERED": "別種",
    "THERIAN": "靈獸", "INCARNATE": "化身",
    "WHITE": "白", "BLACK": "黑",
    "ATTACK": "攻擊", "DEFENSE": "防禦", "SPEED": "速度", "NORMAL": "",
    "SPEED_FORME": "速度",
    # 蒼響/藏瑪然特(劍盾)、蕾冠王(騎乘)、達摩狒狒、凱路迪歐
    "CROWNED": "", "SWORD": "劍之王", "SHIELD": "盾之王",
    "ICE": "冰騎", "RIDER": "", "ZEN": "達摩", "STANDARD": "",
    "FULL": "", "BELLY": "", "HANGRY": "空腹",
    "RESOLUTE": "覺悟", "ORDINARY": "",
}


# ---------------------------------------------------------------- 下載工具

def _mirror_urls(owner_repo, branch, path):
    """依序回傳同一檔案的多個鏡像 URL 與所需 headers。"""
    return [
        (f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{path}", {}),
        (f"https://cdn.jsdelivr.net/gh/{owner_repo}@{branch}/{path}", {}),
        (f"https://api.github.com/repos/{owner_repo}/contents/{path.replace('%20', ' ')}?ref={branch}",
         {"Accept": "application/vnd.github.raw"}),
    ]


def fetch(owner_repo, branch, path, as_json=True, rounds=3, timeout=120):
    """多鏡像輪替 + 指數退避重試下載。429/5xx 換下一個鏡像或退避重試。"""
    last_err = None
    for attempt in range(rounds):
        for url, headers in _mirror_urls(owner_repo, branch, path):
            try:
                r = requests.get(url, headers=headers, timeout=timeout)
                if r.status_code == 200:
                    return r.json() if as_json else r.text
                if r.status_code in (429, 403):
                    wait = int(r.headers.get("Retry-After", 0)) or 0
                    print(f"  [{r.status_code}] {url.split('/')[2]} 被限流,換下一個鏡像…")
                    if wait:
                        time.sleep(min(wait, 30))
                    last_err = requests.HTTPError(f"{r.status_code} @ {url}")
                    continue
                r.raise_for_status()
            except Exception as e:  # 網路錯誤 → 換鏡像
                last_err = e
                continue
        backoff = 2 ** attempt * 3
        print(f"  所有鏡像失敗(第 {attempt + 1} 輪),{backoff}s 後重試…")
        time.sleep(backoff)
    raise RuntimeError(f"下載失敗:{path}({last_err})")


def load_sources(local_dir):
    """載入三個主來源 JSON(寶可夢清單、快招、充能招)。"""
    if local_dir:
        print(f"讀取本地來源:{local_dir}")
        out = []
        for _, _, path in (SRC_PKM, SRC_FM, SRC_CM):
            with open(os.path.join(local_dir, path), encoding="utf-8") as f:
                out.append(json.load(f))
        return out
    print("下載 pokemon-resources 資料 ...")
    return [fetch(*src) for src in (SRC_PKM, SRC_FM, SRC_CM)]


def fetch_src_version():
    """取得 pokemon-resources 最新 commit 版本字串;失敗回 'unknown'。"""
    try:
        c = requests.get(RES_VER_URL, timeout=30).json()
        sha = c.get("sha", "")[:7]
        date = (c.get("commit", {}).get("committer", {}).get("date", "") or "")[:10]
        if sha:
            return f"pokemon-resources@{sha}({date})"
    except Exception:
        pass
    return "unknown"


# ---------------------------------------------------------------- 招式

def move_id(name, is_fast):
    """英文招式名 → GM 風格 move id(快招加 _FAST 後綴)。"""
    mid = MOVE_ID_OVERRIDES.get(name)
    if mid is None:
        s = name.replace("'", "").replace("’", "")
        mid = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return mid + "_FAST" if is_fast else mid


def build_moves(fm, cm):
    """回傳 (moves, move_num, name2id_fast, name2id_charged)。

    moves: {move_id: {...}};move_num: {move_id: 招式數字編號}(繁中對照用);
    name2id_*: 英文招式名 → move id(寶可夢條目的招式表引用用)。
    """
    moves, move_num = {}, {}
    name2id = {True: {}, False: {}}
    for src, is_fast in ((fm, True), (cm, False)):
        for m in src:
            mid = move_id(m["name"], is_fast)
            moves[mid] = {
                "id": mid,
                "type": m["type"].upper(),
                "power": float(m.get("power", 0.0)),
                "energy": m.get("energy_delta", 0),
                "duration": m.get("duration", 0),
                "dws": m.get("damage_window_start", 0),  # 傷害判定開始(一格招懲罰用)
                "is_fast": is_fast,
                "num": m["id"],
            }
            move_num[mid] = m["id"]
            name2id[is_fast][m["name"]] = mid
    return moves, move_num, name2id[True], name2id[False]


# ---------------------------------------------------------------- 寶可夢 id / 形態

def pokemon_id_for(name, dex):
    """英文種族名 → GM 風格 pokemon_id。

    dex >= 984(九世代悖謬/災厄)GM 一律無分隔連寫;其餘非英數段轉底線。
    """
    if name in PID_OVERRIDES:
        return PID_OVERRIDES[name]
    s = name.replace("'", "").replace("’", "")
    if dex >= 984:
        return re.sub(r"[^A-Za-z0-9]", "", s).upper()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()


def form_label(entry):
    """來源 form 值 → GM 風格形態 label(Normal → None)。"""
    f = FORM_ALIASES.get(entry.get("form") or "Normal", entry.get("form") or "Normal")
    if f == "Normal":
        return None
    if f == "Mega":  # Primal Kyogre/Groudon 的 form 也是 "Mega",以 name 前綴區分
        if entry["name"].startswith("Primal "):
            return "PRIMAL"
        return "MEGA_X" if entry["name"].endswith(" X") else "MEGA"
    if f == "MegaY":
        return "MEGA_Y"
    return f.upper()


def en_name(pokemon_id, label):
    base = pokemon_id.replace("_", " ").title()
    if label:
        return f"{label.replace('_', ' ').title()} {base}"
    return base


# ---------------------------------------------------------------- sprite 資源

def _norm(s):
    """名稱/形態正規化:小寫、去所有非英數字元。"""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def load_sprites():
    """下載 sprite 檔名清單。回傳 {norm(檔名去.png): 檔名}。"""
    print("下載 sprite 檔名清單(git tree)...")
    sprite_files = {}
    try:
        tree = requests.get(RES_TREE_URL, timeout=60).json().get("tree", [])
        for x in tree:
            p = x.get("path", "")
            if p.startswith("graphics/pogo-256/") and p.endswith(".png"):
                fname = p.split("/")[-1]
                sprite_files[_norm(fname[:-4])] = fname
    except Exception as e:
        print(f"  [警告] sprite 清單下載失敗,圖示將回退 PokeAPI:{e}")
    print(f"  sprite 檔 {len(sprite_files)}")
    return sprite_files


def resolve_sprite(pokemon_id, label, sprite_files):
    """解析 GO 風格圖示檔名;找不到回傳 None(前端回退 PokeAPI)。"""
    base = _norm(pokemon_id)
    lbl = _norm((label or "").replace("SHADOW", ""))
    for key in ([base + lbl] if lbl else []) + [base]:
        if key in sprite_files:
            return sprite_files[key]
    return None


# ---------------------------------------------------------------- 寶可夢清單

def build_pokemon(pkm, name2id_fast, name2id_charged, sprite_files):
    """回傳寶可夢清單,含各真實形態 + Mega/Primal + Shadow 變體。"""

    # 每個 dex 的 pokemon_id:以 Normal 條目的 name 推導(Mega/Primal 條目 name 帶前綴)
    pid_by_dex = {}
    for e in pkm:
        if (e.get("form") or "Normal") == "Normal" and e["id"] not in pid_by_dex:
            pid_by_dex[e["id"]] = pokemon_id_for(e["name"], e["id"])

    def dangling(names, table):
        return [n for n in names or [] if n not in table]

    # Normal 優先、短 form 優先 → 去重時保留正規形態,丟純外觀(服裝/顏色)重複
    order = sorted(pkm, key=lambda e: (
        e["id"],
        (e.get("form") or "Normal") != "Normal",
        len(e.get("form") or ""),
        e.get("form") or "",
    ))

    entries, seen_sig, seen_uid = [], set(), set()
    missing = 0
    for e in order:
        dex = e["id"]
        pid = pid_by_dex.get(dex)
        if not pid:  # 理論上不會發生(每個 dex 都有 Normal 條目)
            pid = pokemon_id_for(e["name"], dex)
        label = form_label(e)
        if label in EXCLUDE_FORMS:
            continue

        bad = dangling(e.get("fm"), name2id_fast) + dangling(e.get("cm"), name2id_charged) \
            + dangling(e.get("elite_fm"), name2id_fast) + dangling(e.get("elite_cm"), name2id_charged)
        if bad:
            missing += len(bad)
        fast = sorted({name2id_fast[n] for n in e.get("fm") or [] if n in name2id_fast})
        charged = sorted({name2id_charged[n] for n in e.get("cm") or [] if n in name2id_charged})
        ef = sorted({name2id_fast[n] for n in e.get("elite_fm") or [] if n in name2id_fast})
        ec = sorted({name2id_charged[n] for n in e.get("elite_cm") or [] if n in name2id_charged})
        if not fast or not charged:
            continue

        st = e["stats"]
        types = [t.upper() for t in e.get("types") or []]
        sig = (pid, tuple(types), st["baseAttack"], st["baseDefense"], st["baseStamina"],
               tuple(fast), tuple(charged), tuple(ef), tuple(ec))
        uid = pid + (f"_{label}" if label else "")
        if sig in seen_sig or uid in seen_uid:
            continue
        seen_sig.add(sig)
        seen_uid.add(uid)

        is_mega = e.get("form") in ("Mega", "MegaY")  # 含 Primal(form 亦為 Mega)
        entries.append({
            "uid": uid, "pokemon_id": pid, "dex": dex,
            "name_en": en_name(pid, label), "form": label, "types": types,
            "base": {"atk": st["baseAttack"], "def": st["baseDefense"], "sta": st["baseStamina"]},
            "fast": fast, "charged": charged,
            "elite_fast": ef, "elite_charged": ec,
            "is_mega": is_mega, "is_shadow": False,
            "can_shadow": bool(e.get("shadow")) and not is_mega,
            "released": bool(e.get("released")),
            "sprite": resolve_sprite(pid, label, sprite_files),
        })

    # --- Shadow 變體(可暗影化的一般形態;繼承本體 released)---
    shadow_entries = []
    for e in entries:
        if e["can_shadow"] and not e["is_mega"]:
            s = dict(e)
            s["uid"] = e["uid"] + "_SHADOW"
            s["name_en"] = "Shadow " + e["name_en"]
            s["form"] = (e["form"] + "_SHADOW") if e["form"] else "SHADOW"
            s["is_shadow"] = True
            shadow_entries.append(s)
    entries.extend(shadow_entries)
    if missing:
        print(f"  [提示] {missing} 個招式名在招式表中對不到,已忽略")
    return entries


# ---------------------------------------------------------------- 繁中名稱

def build_names(pokemon, move_num):
    print("下載繁中文字 ...")
    raw = fetch(*ZH_REPO)["data"]
    kv = {raw[i]: raw[i + 1] for i in range(0, len(raw) - 1, 2)}

    zh = {"pokemon": {}, "move": {}, "form": FORM_LABEL_ZH}
    for e in pokemon:
        pid = e["pokemon_id"]
        if pid in zh["pokemon"]:
            continue
        key = f"pokemon_name_{e['dex']:04d}"
        if key in kv:
            zh["pokemon"][pid] = kv[key]
    for mid, num in move_num.items():
        key = f"move_name_{num:04d}"
        if key in kv:
            zh["move"][mid] = kv[key]
    return zh


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", help="本地來源目錄(含 pogo_pkm.min.json / pogo_fm.json / pogo_cm.json,離線用)")
    args = ap.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    has_old = os.path.exists(os.path.join(DATA_DIR, "pokemon.json"))

    try:
        pkm, fm, cm = load_sources(args.local)
        version = "local" if args.local else fetch_src_version()
        moves, move_num, name2id_fast, name2id_charged = build_moves(fm, cm)
        print(f"招式:{len(moves)} 個")
        sprite_files = load_sprites()
        pokemon = build_pokemon(pkm, name2id_fast, name2id_charged, sprite_files)
        n_rel = sum(1 for e in pokemon if e["released"])
        n_spr = sum(1 for e in pokemon if e["sprite"])
        print(f"寶可夢條目:{len(pokemon)} 筆(已實裝 {n_rel}、有 GO 圖示 {n_spr})")
        names = build_names(pokemon, move_num)
        print(f"繁中名稱:寶可夢 {len(names['pokemon'])}、招式 {len(names['move'])}")
    except Exception as e:
        if has_old:
            print(f"\n[錯誤] 更新失敗:{e}\n已保留既有的 data/ 快照,程式仍可正常使用。")
            sys.exit(1)
        raise

    def dump(name, obj):
        path = os.path.join(DATA_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  寫入 {path}({os.path.getsize(path) // 1024} KB)")

    dump("moves.json", moves)
    dump("pokemon.json", pokemon)
    dump("names_zh_tw.json", names)
    dump("meta.json", {
        "gm_version": version,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "counts": {"pokemon": len(pokemon), "moves": len(moves)},
    })
    print("完成。")


if __name__ == "__main__":
    main()
