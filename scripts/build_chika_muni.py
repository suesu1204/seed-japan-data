"""③-2/③-3: 지가공시 지점 CSV → 시정촌×연도 집계 → 과소지역 인구 패널에 결합.

입력: output/chika_points/chika_YYYY.csv (③-1), scripts/code_map_2010_2026.csv (3단계 대응표), 과소지역_매칭/jp_pop_kaso.csv (5단계)
출력: output/chika_muni.csv           전국 (year, muni_code) 집계. muni_code는 2026년 기준
      output/chika_kaso.csv           과소 727곳×17년 지가공시만 (식별 6열 + 집계 19열)
"""
import glob, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PTS = os.path.join(ROOT, "output", "chika_points")
MAP = os.path.join(ROOT, "scripts", "code_map_2010_2026.csv")
KASO = os.path.join(ROOT, "과소지역_매칭", "jp_pop_kaso.csv")  # 5단계 출력 (사용자가 폴더 이동)
OUT_MUNI = os.path.join(ROOT, "output", "chika_muni.csv")
OUT_KASO = os.path.join(ROOT, "output", "chika_kaso.csv")  # 과소 727곳 × 17년, 공시지가만 (인구와 합치지 않음)
USE_CODES = ["000", "003", "005", "007", "009", "010", "013"]

pts = pd.concat([pd.read_csv(f, dtype={"muni_code": str, "use_code": str, "seq": str}) for f in sorted(glob.glob(os.path.join(PTS, "chika_*.csv")))], ignore_index=True)
assert set(pts.year) == set(range(2010, 2027)) and set(pts.use_code) <= set(USE_CODES)
n_in = len(pts)

# 3단계 대응표로 2026년 코드 통일. 지가공시는 연도 조건 없이 코드만으로 적용한다
# (옛 코드는 재사용되지 않음. 기준일이 1/1이라 인구(3/31)보다 합병 반영이 늦는 해가 있음: 2010년 33곳, 2012년 長久手町).
# 43341→43201→43100 같은 연쇄는 바뀌는 코드가 없을 때까지 반복.
cmap = pd.read_csv(MAP, dtype=str).fillna("")
mp = cmap[cmap.new_code != ""].set_index("old_code").new_code
pts["muni_code_orig"] = pts.muni_code
for _ in range(5):
    hit = pts.muni_code.isin(mp.index)
    if not hit.any():
        break
    pts.loc[hit, "muni_code"] = pts.loc[hit, "muni_code"].map(mp)
panel_codes = set(pd.read_csv(os.path.join(ROOT, "output", "jp_pop_2026basis.csv"), dtype={"muni_code": str}).muni_code)
panel_codes |= {"14150", "43100", "22130"}  # 3단계 C·D: 정령시 합계 코드 (인구 출력 3에 있음)
orphan = pts[~pts.muni_code.isin(panel_codes)]
assert orphan.empty, orphan.groupby(["year", "muni_code"]).size()
print(f"코드 통일 적용 지점: {(pts.muni_code != pts.muni_code_orig).sum()}")

# (year, muni_code) 집계
g = pts.groupby(["year", "muni_code"])
agg = g.agg(n_points=("price_per_sqm", "size"),
            price_median=("price_per_sqm", "median"),
            price_mean=("price_per_sqm", "mean"),
            price_min=("price_per_sqm", "min"),
            price_max=("price_per_sqm", "max"))
for u in USE_CODES:
    s = pts[pts.use_code == u].groupby(["year", "muni_code"]).price_per_sqm
    agg[f"n_u{u}"] = s.size()
    agg[f"med_u{u}"] = s.median()
agg = agg.reset_index()
for c in [c for c in agg.columns if c.startswith("n_")]:
    agg[c] = agg[c].fillna(0).astype(int)
assert agg.n_points.sum() == n_in and not agg.duplicated(["year", "muni_code"]).any()
assert (agg[[f"n_u{u}" for u in USE_CODES]].sum(axis=1) == agg.n_points).all()
agg.to_csv(OUT_MUNI, index=False, encoding="utf-8-sig")

# 과소지역 패널에 결합 (left join: 인구 행은 전부 유지, 지점 없는 곳은 NA)
kaso = pd.read_csv(KASO, dtype={"muni_code": str, "city_code": str})
join = kaso.merge(agg, on=["year", "muni_code"], how="left")
assert len(join) == len(kaso) == 727 * 17
join["n_points"] = join.n_points.fillna(0).astype(int)
for c in [c for c in join.columns if c.startswith("n_u")]:
    join[c] = join[c].fillna(0).astype(int)
# 공시지가 단독 파일: 식별 6열 + 집계 19열, 행 순서는 jp_pop_kaso.csv와 동일
solo = join[["year", "muni_code", "pref", "muni", "row_type", "city_code"] + list(agg.columns.drop(["year", "muni_code"]))].copy()
for c in [c for c in solo.columns if c.startswith(("price_", "med_"))]:
    solo[c] = solo[c].round().astype("Int64")
solo.to_csv(OUT_KASO, index=False, encoding="utf-8-sig")

# 커버리지 보고
cov = join.groupby("year").agg(muni_with_points=("n_points", lambda s: (s > 0).sum()), points=("n_points", "sum"))
print(cov.T.to_string())
never = join.groupby("muni_code").n_points.sum()
never = never[never == 0]
always = (join.groupby("muni_code").n_points.min() > 0).sum()
print(f"727곳 중 17년 전부 지점 있음: {always} | 17년 내내 지점 없음: {len(never)}")
print(f"saved → {OUT_MUNI} {agg.shape}, {OUT_KASO} {solo.shape}")
