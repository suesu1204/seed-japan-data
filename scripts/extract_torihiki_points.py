"""②-1: reinfolib XIT001 원본 JSON → 연도별 거래 CSV 17개.

입력: Reinfolib/raw/XIT001_{year}_{q}_{area}.json
출력: output/torihiki_points/torihiki_YYYY.csv   (거래 1건 = 1행, 11열)

원본 항목 이름은 아래 FIELDS에 명시. 없으면 추측하지 않고 멈춘다.
숫자 열에 숫자가 아닌 값이 오면(구간 표기 등) 멈추고 보고한다.
"""
import csv, glob, json, os, re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "Reinfolib", "raw")
OUT = os.path.join(ROOT, "output", "torihiki_points")
FIELDS = ["Type", "Region", "MunicipalityCode", "TradePrice", "Area", "UnitPrice", "TotalFloorArea", "BuildingYear", "Period"]
COLS = ["year", "quarter", "muni_code", "type", "region", "trade_price", "area_sqm", "unit_price", "price_per_sqm", "floor_area_sqm", "building_year"]
TYPES = {"宅地(土地)", "宅地(土地と建物)", "中古マンション等", "農地", "林地"}


def num(s, where):
    """빈칸→None, 정수 문자열→int. 그 외(구간 표기 등)는 멈춤."""
    if s == "":
        return None
    assert re.fullmatch(r"\d+", s), (where, repr(s))
    return int(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RAW, "XIT001_*.json")))
    by_year = {}
    for f in files:
        fy, fq, fa = re.search(r"XIT001_(\d{4})_(\d)_(\d{2})\.json$", f).groups()
        body = json.loads(open(f, "rb").read().decode("utf-8-sig"))
        assert body["status"] == "OK", f
        for r in body["data"]:
            missing = [k for k in FIELDS if k not in r]
            assert not missing, (f, missing)
            m = re.fullmatch(r"(\d{4})年第(\d)四半期", r["Period"])
            assert m and m.group(1) == fy and m.group(2) == fq, (f, r["Period"])
            code = r["MunicipalityCode"].zfill(5)  # 도도부현 01~09는 앞 0이 빠진 4자리로 옴 (0 채운 뒤 파일 도도부현과 100% 일치 확인)
            assert re.fullmatch(r"\d{5}", code) and code[:2] == fa, (f, r["MunicipalityCode"])
            assert r["Type"] in TYPES, (f, r["Type"])
            tp, ar = num(r["TradePrice"], (f, "TradePrice")), num(r["Area"], (f, "Area"))
            by_year.setdefault(int(fy), []).append(dict(
                year=int(fy), quarter=int(fq), muni_code=code, type=r["Type"], region=r["Region"],
                trade_price=tp, area_sqm=ar, unit_price=num(r["UnitPrice"], (f, "UnitPrice")),
                price_per_sqm=(round(tp / ar) if tp is not None and ar else None),
                floor_area_sqm=num(r["TotalFloorArea"], (f, "TotalFloorArea")), building_year=r["BuildingYear"],
            ))
    total = 0
    for y, rows in sorted(by_year.items()):
        with open(os.path.join(OUT, f"torihiki_{y}.csv"), "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(rows)
        total += len(rows)
        c = Counter(r["type"] for r in rows)
        print(f"{y}: {len(rows):7d}건 | {dict(c)}")
    print(f"총 {total}건, 파일 {len(files)}개 →", OUT)


if __name__ == "__main__":
    main()
