"""소득 통제변수 1번. e-Stat API로 社会・人口統計体系 시구정촌 데이터(합병 처리판, 표 0000020203)에서
C120110 課税対象所得(천 엔), C120120 納税義務者数(所得割) 를 받아 원본 JSON 저장 + 긴 형식 csv.
appId 는 .env 의 ESTAT_APP_ID (또는 환경변수). 파일에 기록하지 않음.
출력: raw/meta_0000020203.json, raw/data_0000020203_*.json, income_raw.csv (area_code, area_name, year, item, item_name, value, unit)
"""
import json, os, sys, time, urllib.parse, urllib.request, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "raw")
def load_env():
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1); os.environ.setdefault(k.strip(), v.strip())
load_env()
APP = os.environ.get("ESTAT_APP_ID"); assert APP, "ESTAT_APP_ID 없음 (.env 확인)"
BASE = "https://api.e-stat.go.jp/rest/3.0/app/json/"
TABLE = "0000020203"; ITEMS = ["C120110", "C120120"]

def get(endpoint, **params):
    params["appId"] = APP
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

# ---- 메타: 분류 축 확인 ----
meta = get("getMetaInfo", statsDataId=TABLE)
json.dump(meta, open(os.path.join(RAW, f"meta_{TABLE}.json"), "w", encoding="utf-8"), ensure_ascii=False)
res = meta["GET_META_INFO"]["RESULT"]; assert res["STATUS"] == 0, res
classes = meta["GET_META_INFO"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]
print("표:", meta["GET_META_INFO"]["METADATA_INF"]["TABLE_INF"]["TITLE"] if "TITLE" in meta["GET_META_INFO"]["METADATA_INF"]["TABLE_INF"] else "")
for c in classes:
    items = c["CLASS"] if isinstance(c["CLASS"], list) else [c["CLASS"]]
    print(f"  축 {c['@id']} ({c['@name']}): {len(items)}개")
cat_axis = [c for c in classes if c["@id"].startswith("cat")]
# 항목 코드가 들어있는 축 찾기
item_axis = None
for c in cat_axis:
    items = c["CLASS"] if isinstance(c["CLASS"], list) else [c["CLASS"]]
    codes = {i["@code"] for i in items}
    if set(ITEMS) <= codes:
        item_axis = c["@id"]; names = {i["@code"]: i["@name"] for i in items if i["@code"] in ITEMS}; break
assert item_axis, "C120110/C120120 가 있는 축을 못 찾음"
print("항목 축:", item_axis, names)
time_axis = [c for c in classes if c["@id"] == "time"][0]
times = time_axis["CLASS"] if isinstance(time_axis["CLASS"], list) else [time_axis["CLASS"]]
print("시간 축:", times[0]["@code"], times[0]["@name"], "~", times[-1]["@code"], times[-1]["@name"], f"({len(times)}개)")
area_axis = [c for c in classes if c["@id"] == "area"][0]
areas = area_axis["CLASS"] if isinstance(area_axis["CLASS"], list) else [area_axis["CLASS"]]
area_name = {a["@code"]: a["@name"] for a in areas}; print("지역 수:", len(areas), "| 예:", areas[0], areas[-1])

# ---- 데이터: 항목 2개, 전체 지역, 2009년도 이후 ----
rows = []; start = 1; k = 0
while True:
    d = get("getStatsData", statsDataId=TABLE, **{"cd" + item_axis[0].upper() + item_axis[1:]: ",".join(ITEMS)}, limit=100000, startPosition=start, metaGetFlg="N")
    k += 1; json.dump(d, open(os.path.join(RAW, f"data_{TABLE}_{k}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    r = d["GET_STATS_DATA"]["RESULT"]; assert r["STATUS"] == 0, r
    inf = d["GET_STATS_DATA"]["STATISTICAL_DATA"]["RESULT_INF"]
    vals = d["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
    rows += vals if isinstance(vals, list) else [vals]
    print(f"  호출 {k}: {inf['FROM_NUMBER']}~{inf['TO_NUMBER']} / 전체 {inf['TOTAL_NUMBER']}")
    if "NEXT_KEY" not in inf: break
    start = int(inf["NEXT_KEY"]); time.sleep(1)

tk = "@" + item_axis
with open(os.path.join(HERE, "income_raw.csv"), "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh); w.writerow(["area_code", "area_name", "year", "item", "item_name", "value", "unit"])
    for v in rows:
        w.writerow([v["@area"], area_name.get(v["@area"], ""), v["@time"], v[tk], names[v[tk]], v["$"], v.get("@unit", "")])
print("income_raw.csv", len(rows), "행")
