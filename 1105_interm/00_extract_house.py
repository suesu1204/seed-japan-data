"""1105_interm 1단계: reinfolib 원본 JSON에서 토지+건물(宅地(土地と建物)) 거래만 속성 포함 추출.
기존 output/torihiki_points 에는 Use(건물 용도)·Purpose·Structure 가 없어 원본에서 다시 뽑는다.
입력 Reinfolib/raw/XIT001_{year}_{q}_{pref}.json   출력 house_trades.csv (거래 1건 = 1행)
숫자 열: 빈칸→결측, 정수 문자열만 허용(그 외는 멈춤). 2026년은 1분기뿐이라 제외.
"""
import csv, glob, json, os, re
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "Reinfolib", "raw")
FIELDS = ["Type", "Region", "Use", "Purpose", "Structure", "MunicipalityCode", "TradePrice", "Area", "TotalFloorArea", "BuildingYear", "Period"]
COLS = ["year", "quarter", "muni_code", "region", "use", "purpose", "structure", "trade_price", "area_sqm", "floor_area_sqm", "building_year"]

def num(s, where):
    if s == "": return None
    assert re.fullmatch(r"\d+", s), (where, repr(s)); return int(s)

files = sorted(glob.glob(os.path.join(RAW, "XIT001_*.json")))
rows, use_c, reg_c = [], Counter(), Counter()
for f in files:
    fy, fq, fa = re.search(r"XIT001_(\d{4})_(\d)_(\d{2})\.json$", f).groups()
    if int(fy) > 2025: continue
    body = json.loads(open(f, "rb").read().decode("utf-8-sig")); assert body["status"] == "OK", f
    for r in body["data"]:
        if r["Type"] != "宅地(土地と建物)": continue
        assert all(k in r for k in FIELDS), (f, [k for k in FIELDS if k not in r])
        m = re.fullmatch(r"(\d{4})年第(\d)四半期", r["Period"]); assert m and m.group(1) == fy and m.group(2) == fq, (f, r["Period"])
        code = r["MunicipalityCode"].zfill(5); assert code[:2] == fa, (f, code)
        rows.append(dict(year=int(fy), quarter=int(fq), muni_code=code, region=r["Region"], use=r["Use"], purpose=r["Purpose"], structure=r["Structure"],
                         trade_price=num(r["TradePrice"], (f, "TradePrice")), area_sqm=num(r["Area"], (f, "Area")),
                         floor_area_sqm=num(r["TotalFloorArea"], (f, "TotalFloorArea")), building_year=r["BuildingYear"]))
        use_c[r["Use"]] += 1; reg_c[r["Region"]] += 1
with open(os.path.join(HERE, "house_trades.csv"), "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(rows)
print("house_trades.csv", len(rows), "건, 파일", len(files))
print("Region:", reg_c.most_common())
print("Use 상위 20:", use_c.most_common(20))
print("floor_area 결측:", sum(r["floor_area_sqm"] is None for r in rows), "| area 9999:", sum(r["area_sqm"] == 9999 for r in rows), "| floor 9999:", sum(r["floor_area_sqm"] == 9999 for r in rows))
