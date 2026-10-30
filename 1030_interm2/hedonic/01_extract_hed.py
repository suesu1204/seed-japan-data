"""헤도닉 1번. reinfolib 원본 JSON 재추출 (v2 기준: unit_price 포함). 다운로드 없음.

입력: Reinfolib/raw/XIT001_{year}_{q}_{pref}.json  (2010~2025만 사용)
출력: 1030_interm2/hedonic/torihiki_hed.csv  — 宅地(土地)·中古マンション等 거래 건별
열: year, quarter, muni_code, type, trade_price, area_sqm, unit_price, building_year, city_planning, breadth
     원본 문자열 그대로. 변환·제외 없음 (변수 만들기는 02에서).
규칙: 항목 없으면 멈춤. TradePrice·Area가 숫자가 아니면 멈춤.
"""
import csv, glob, json, os, re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Data/
RAW = os.path.join(ROOT, "Reinfolib", "raw")
HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["Type", "MunicipalityCode", "TradePrice", "Area", "UnitPrice", "BuildingYear", "Period", "CityPlanning", "Breadth"]
COLS = ["year", "quarter", "muni_code", "type", "trade_price", "area_sqm", "unit_price", "building_year", "city_planning", "breadth"]
TYPES = {"宅地(土地)", "中古マンション等"}


def num(s, where):
    if s == "":
        return ""
    assert re.fullmatch(r"\d+", s), (where, repr(s))
    return int(s)


assert os.path.isdir(RAW), RAW
rows, n_files = [], 0
for f in sorted(glob.glob(os.path.join(RAW, "XIT001_*.json"))):
    fy, fq, fa = re.search(r"XIT001_(\d{4})_(\d)_(\d{2})\.json$", f).groups()
    if not 2010 <= int(fy) <= 2025:
        continue
    n_files += 1
    body = json.loads(open(f, "rb").read().decode("utf-8-sig"))
    assert body["status"] == "OK", f
    for r in body["data"]:
        if r.get("Type") not in TYPES:
            continue
        missing = [k for k in FIELDS if k not in r]
        assert not missing, (f, missing)
        code = r["MunicipalityCode"].zfill(5)
        assert re.fullmatch(r"\d{5}", code) and code[:2] == fa, (f, r["MunicipalityCode"])
        rows.append(dict(year=int(fy), quarter=int(fq), muni_code=code, type=r["Type"],
                         trade_price=num(r["TradePrice"], (f, "TradePrice")), area_sqm=num(r["Area"], (f, "Area")),
                         unit_price=num(r["UnitPrice"], (f, "UnitPrice")), building_year=r["BuildingYear"],
                         city_planning=r["CityPlanning"], breadth=r["Breadth"]))

out = os.path.join(HERE, "torihiki_hed.csv")
with open(out, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(rows)
c = Counter(r["type"] for r in rows)
print(f"파일 {n_files}개 → {len(rows):,}건", dict(c))
assert c["宅地(土地)"] == 1668802 and c["中古マンション等"] == 826348, "v2 패널 건수와 불일치"
assert all(r["unit_price"] != "" for r in rows if r["type"] == "宅地(土地)"), "토지만 UnitPrice 결측"
print("검증 통과: 건수 = v2 패널, 토지만 UnitPrice 결측 0")
