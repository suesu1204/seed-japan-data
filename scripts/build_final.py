"""최종 파일 생성 (final_result2/). 단위 = 시정촌 + 도쿄 23구 (정령시는 시 전체), 전국, 2010~2026.

입력
  output/population_typed/jp_pop_typed_YYYY.csv   2단계 (모든 행 + row_type, city_code)
  scripts/code_map_2010_2026.csv                   3단계 대응표
  과소지역_매칭/kaso_match.csv                      과소지역 885곳 구분
  output/chika_points/chika_YYYY.csv               ③-1 지가공시 지점
  output/torihiki_points/torihiki_YYYY.csv         ②-1 실거래 건별
출력 (final_result2/)
  jp_pop.csv          한국 korea_population 파일과 같은 12열 + kaso
  jp_pop_detail.csv   5세 단위·남녀 원자료 69열
  chika.csv           공시지가 집계 (용도 이름 영문)
  torihiki.csv        실거래 건별 전국 (원본 항목만). 깃허브 제외
  muni_names.csv      코드·이름·종류·과소 구분
"""
import glob, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "final_result2")
os.makedirs(OUT, exist_ok=True)
YEARS = list(range(2010, 2027))
UNIT = ["ward", "special_ward", "city", "town", "village"]
S = {"muni_code": str, "muni_code_6digit": str, "city_code": str, "muni": str}

# ---------- 대응표: 코드만으로 적용, 연쇄 추적 ----------
cmap = pd.read_csv(os.path.join(ROOT, "scripts", "code_map_2010_2026.csv"), dtype=str).fillna("")
MP = cmap[cmap.new_code != ""].set_index("old_code").new_code


def to_2026(codes):
    codes = codes.copy()
    for _ in range(5):
        hit = codes.isin(MP.index)
        if not hit.any():
            break
        codes[hit] = codes[hit].map(MP)
    return codes


# ---------- 2026년 단위 집합: 시정촌 + 도쿄 23구 ----------
t26 = pd.read_csv(os.path.join(ROOT, "output", "population_typed", "jp_pop_typed_2026.csv"), dtype=S)
t26["muni"] = t26.muni.fillna("")
WARD_TO_CITY = t26.loc[t26.row_type == "ward"].set_index("muni_code").city_code      # 구 → 정령시
keep26 = t26[t26.row_type.isin(["city_agg", "special_ward", "city", "town", "village"])]
names = keep26[["muni_code", "pref", "muni", "row_type"]].copy()
names["row_type"] = names.row_type.replace({"city_agg": "city"})
kaso = pd.read_csv(os.path.join(ROOT, "과소지역_매칭", "kaso_match.csv"), dtype={"muni_code": str})
names = names.merge(kaso[["muni_code", "kaso_kind"]], on="muni_code", how="left").rename(columns={"kaso_kind": "kaso"})
names["kaso"] = names.kaso.fillna("非該当")
UNITS = set(names.muni_code)
assert len(UNITS) == 1741 and names.kaso.value_counts().to_dict()["全部過疎"] == 713


def unitize(codes):
    """2026 코드 → 시정촌 단위 코드 (정령시의 구는 소속 시로)."""
    c = to_2026(codes)
    return c.where(~c.isin(WARD_TO_CITY.index), c.map(WARD_TO_CITY))


# ---------- 인구 ----------
POP = None
rows = []
for y in YEARS:
    d = pd.read_csv(os.path.join(ROOT, "output", "population_typed", f"jp_pop_typed_{y}.csv"), dtype=S)
    if POP is None:
        POP = [c for c in d.columns if c.startswith(("pop_", "age_"))]
    u = d[d.row_type.isin(UNIT)].copy()
    u["unit"] = unitize(u.muni_code)
    bad = u[~u.unit.isin(UNITS)]
    assert bad.empty, (y, bad[["muni_code", "muni"]].drop_duplicates().head())
    g = u.groupby("unit")[POP].sum(min_count=1)
    g.insert(0, "year", y)
    # 검사: 도도부현 합계 = 단위 합
    pref_tot = d[d.row_type == "pref"].set_index(d[d.row_type == "pref"].muni_code.str[:2]).pop_total
    unit_tot = g.pop_total.groupby(g.index.str[:2]).sum()
    assert (pref_tot.sort_index() == unit_tot.sort_index()).all(), y
    rows.append(g.reset_index().rename(columns={"unit": "muni_code"}))
detail = pd.concat(rows, ignore_index=True)
assert len(detail) == 1741 * 17 and not detail.duplicated(["year", "muni_code"]).any()
assert detail.groupby("muni_code").size().eq(17).all()
for c in POP:
    detail[c] = detail[c].astype("Int64")
detail = detail.sort_values(["muni_code", "year"]).reset_index(drop=True)

def grp(cols):
    return detail[cols].sum(axis=1)
pop = pd.DataFrame({
    "muni_code": detail.muni_code, "year": detail.year, "total_pop": detail.pop_total,
    "child_pop": grp(["age_0_4", "age_5_9", "age_10_14"]),
    "youth_pop": grp(["age_15_19", "age_20_24", "age_25_29", "age_30_34"]),
    "middle_pop": grp(["age_35_39", "age_40_44", "age_45_49", "age_50_54", "age_55_59", "age_60_64"]),
    "elderly_pop": grp(["age_65_69", "age_70_74", "age_75_79", "age_80p"]),
})
for k in ["child", "youth", "middle", "elderly"]:
    pop[f"{k}_rate"] = pop[f"{k}_pop"] / pop.total_pop * 100
pop["aging_rate"] = pop.elderly_rate
pop = pop.merge(names[["muni_code", "kaso"]], on="muni_code")
pop = pop[["muni_code", "year", "total_pop", "child_pop", "child_rate", "youth_pop", "youth_rate",
           "middle_pop", "middle_rate", "elderly_pop", "elderly_rate", "aging_rate", "kaso"]]
gap = (pop.total_pop - pop[["child_pop", "youth_pop", "middle_pop", "elderly_pop"]].sum(axis=1)).abs() / pop.total_pop
assert gap.max() < 0.002, gap.max()   # 연령불상자 차이
pop.to_csv(os.path.join(OUT, "jp_pop.csv"), index=False, encoding="utf-8-sig")
detail[["year", "muni_code"] + POP].to_csv(os.path.join(OUT, "jp_pop_detail.csv"), index=False, encoding="utf-8-sig")

# ---------- 공시지가 ----------
pts = pd.concat([pd.read_csv(f, dtype={"muni_code": str, "use_code": str, "seq": str}) for f in sorted(glob.glob(os.path.join(ROOT, "output", "chika_points", "chika_*.csv")))], ignore_index=True)
n_pts = len(pts)
pts["muni_code"] = unitize(pts.muni_code)
assert pts.muni_code.isin(UNITS).all(), pts[~pts.muni_code.isin(UNITS)].muni_code.unique()[:10]
USE = {"000": "residential", "003": "prospective", "005": "commercial", "007": "semi_industrial",
       "009": "industrial", "010": "uca_residential", "013": "uca_forest"}
g = pts.groupby(["year", "muni_code"])
ch = pd.DataFrame({"n_points": g.size(), "price_median": g.price_per_sqm.median(), "price_mean": g.price_per_sqm.mean(),
                   "price_min": g.price_per_sqm.min(), "price_max": g.price_per_sqm.max()})
for code, nm in USE.items():
    s = pts[pts.use_code == code].groupby(["year", "muni_code"]).price_per_sqm
    ch[f"n_{nm}"] = s.size()
    ch[f"med_{nm}"] = s.median()
ch = ch.reset_index()
assert ch.n_points.sum() == n_pts and (ch[[f"n_{n}" for n in USE.values()]].sum(axis=1) == ch.n_points).all()
chika = pop[["year", "muni_code"]].merge(ch, on=["year", "muni_code"], how="left")
for c in chika.columns:
    if c.startswith("n_"):
        chika[c] = chika[c].fillna(0).astype(int)
    elif c.startswith(("price_", "med_")):
        chika[c] = chika[c].round().astype("Int64")
chika.to_csv(os.path.join(OUT, "chika.csv"), index=False, encoding="utf-8-sig")

# ---------- 실거래 (건별, 원본 항목만) ----------
tr = pd.concat([pd.read_csv(f, dtype={"muni_code": str, "building_year": str}) for f in sorted(glob.glob(os.path.join(ROOT, "output", "torihiki_points", "torihiki_*.csv")))], ignore_index=True)
n_tr = len(tr)
tr["muni_code"] = unitize(tr.muni_code)
assert tr.muni_code.isin(UNITS).all()
tr = tr[["year", "quarter", "muni_code", "type", "region", "trade_price", "area_sqm", "unit_price", "floor_area_sqm", "building_year"]]
for c in ["unit_price", "floor_area_sqm"]:
    tr[c] = tr[c].astype("Int64")
tr = tr.sort_values(["year", "quarter", "muni_code"]).reset_index(drop=True)
tr.to_csv(os.path.join(OUT, "torihiki.csv"), index=False, encoding="utf-8-sig")

names.sort_values("muni_code").to_csv(os.path.join(OUT, "muni_names.csv"), index=False, encoding="utf-8-sig")

print("units", len(UNITS), "| jp_pop", pop.shape, "| detail", detail.shape, "| chika", chika.shape, f"(points {n_pts})", "| torihiki", tr.shape, f"(= {n_tr})")
print("kaso:", names.kaso.value_counts().to_dict())
print("row_type:", names.row_type.value_counts().to_dict())
print("chika 지점 있는 단위-연도:", int((chika.n_points > 0).sum()), "/", len(chika))
