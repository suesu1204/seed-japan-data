"""②-2/②-3: 실거래 CSV → 시정촌×연도 집계 → 과소지역 727곳만 별도 파일.

입력: output/torihiki_points/torihiki_YYYY.csv (②-1), scripts/code_map_2010_2026.csv, 과소지역_매칭/jp_pop_kaso.csv (727곳 코드·행 순서)
출력: output/torihiki_muni.csv     전국 (year, muni_code) 집계. muni_code는 2026년 기준
      output/torihiki_kaso.csv     과소 727곳 × 17년. 인구 파일과 행 순서·year·muni_code 동일. 인구와 합치지 않음
"""
import glob, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PTS = os.path.join(ROOT, "output", "torihiki_points")
MAP = os.path.join(ROOT, "scripts", "code_map_2010_2026.csv")
KASO = os.path.join(ROOT, "과소지역_매칭", "jp_pop_kaso.csv")
OUT_MUNI = os.path.join(ROOT, "output", "torihiki_muni.csv")
OUT_KASO = os.path.join(ROOT, "output", "torihiki_kaso.csv")
# 부동산 종류(원본 Type) → 열 접미사
TYPES = {"宅地(土地)": "land", "宅地(土地と建物)": "landbldg", "中古マンション等": "condo", "農地": "farm", "林地": "forest"}

pts = pd.concat([pd.read_csv(f, dtype={"muni_code": str, "building_year": str}) for f in sorted(glob.glob(os.path.join(PTS, "torihiki_*.csv")))], ignore_index=True)
assert set(pts.type) == set(TYPES) and set(pts.year) <= set(range(2010, 2027))
n_in = len(pts)

# 2026년 코드로 통일 (③과 같은 규칙: 연도 조건 없이 코드만, 연쇄 추적, 남는 코드 없어야 함)
cmap = pd.read_csv(MAP, dtype=str).fillna("")
mp = cmap[cmap.new_code != ""].set_index("old_code").new_code
pts["muni_code_orig"] = pts.muni_code
for _ in range(5):
    hit = pts.muni_code.isin(mp.index)
    if not hit.any():
        break
    pts.loc[hit, "muni_code"] = pts.loc[hit, "muni_code"].map(mp)
panel = pd.read_csv(os.path.join(ROOT, "output", "jp_pop_2026basis.csv"), dtype={"muni_code": str})
panel_codes = set(panel.muni_code) | {"14150", "43100", "22130"}
orphan = pts[~pts.muni_code.isin(panel_codes)]
assert orphan.empty, orphan.groupby(["year", "muni_code"]).size().sort_values(ascending=False).head(20)
print(f"코드 통일 적용 거래: {(pts.muni_code != pts.muni_code_orig).sum()}")

# (year, muni_code) 집계: 전체 건수 + 종류별 건수·㎡당 가격 중앙값
g = pts.groupby(["year", "muni_code"])
agg = pd.DataFrame({"n_trades": g.size()})
for t, suf in TYPES.items():
    s = pts[pts.type == t].groupby(["year", "muni_code"])
    agg[f"n_{suf}"] = s.size()
    agg[f"med_ppsqm_{suf}"] = s.price_per_sqm.median()
agg[f"med_unit_land"] = pts[pts.type == "宅地(土地)"].groupby(["year", "muni_code"]).unit_price.median()  # 원본 UnitPrice (토지만 거래)
agg = agg.reset_index()
for c in [c for c in agg.columns if c.startswith("n_")]:
    agg[c] = agg[c].fillna(0).astype(int)
for c in [c for c in agg.columns if c.startswith("med_")]:
    agg[c] = agg[c].round().astype("Int64")
assert agg.n_trades.sum() == n_in and not agg.duplicated(["year", "muni_code"]).any()
assert (agg[[f"n_{s}" for s in TYPES.values()]].sum(axis=1) == agg.n_trades).all()
agg.to_csv(OUT_MUNI, index=False, encoding="utf-8-sig")

# 과소 727곳 × 17년, 인구 파일과 같은 행 순서. 지점 없는 해는 n_*=0, 가격 빈칸
kaso = pd.read_csv(KASO, dtype={"muni_code": str, "city_code": str}, usecols=["year", "muni_code", "pref", "muni", "row_type", "city_code"])
out = kaso.merge(agg, on=["year", "muni_code"], how="left")
assert len(out) == len(kaso) == 727 * 17
for c in [c for c in out.columns if c.startswith("n_")]:
    out[c] = out[c].fillna(0).astype(int)
out.to_csv(OUT_KASO, index=False, encoding="utf-8-sig")

cov = out.groupby("year").agg(muni_with_trades=("n_trades", lambda s: (s > 0).sum()), trades=("n_trades", "sum"))
print(cov.T.to_string())
never = (out.groupby("muni_code").n_trades.sum() == 0).sum()
always = (out.groupby("muni_code").n_trades.min() > 0).sum()
print(f"727곳 중 17년 전부 거래 있음: {always} | 17년 내내 거래 없음: {never}")
print(f"saved → {OUT_MUNI} {agg.shape}, {OUT_KASO} {out.shape}")
