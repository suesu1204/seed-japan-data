"""3단계: 2단계 파일 17개를 대응표(code_map_2010_2026.csv)로 2026년 코드 기준에 맞춰 합친다.

출력 1  output/jp_pop_2026basis.csv            분석용. 단위 행을 (year, 2026 코드)로 묶어 더함. 76컬럼
출력 2  output/jp_pop_2026basis_with_std.csv   기록용. 출력 1 + std 4컬럼. 80컬럼
출력 3  output/jp_pop_2026basis_excluded.csv   2026년 구로 쪼갤 수 없어 뺀 행 (C·D). 2단계 컬럼 + std_note
"""
import glob, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "output", "population_typed")
MAP = os.path.join(ROOT, "scripts", "code_map_2010_2026.csv")
OUT1 = os.path.join(ROOT, "output", "jp_pop_2026basis.csv")
OUT2 = os.path.join(ROOT, "output", "jp_pop_2026basis_with_std.csv")
OUT3 = os.path.join(ROOT, "output", "jp_pop_2026basis_excluded.csv")

UNIT = ["ward", "special_ward", "city", "town", "village"]
EXCLUDE_NOTES = ["C_designated_city", "D_ward_reorg"]
# 출력 1에서 비는 자리(2026년 구가 그 해에 없었음)
EXPECTED_GAPS = {y: set() for y in range(2010, 2027)}
for y in [2010]:
    EXPECTED_GAPS[y] |= {"14151", "14152", "14153"}                      # 相模原 구, 2011 승격
for y in [2010, 2011, 2012]:
    EXPECTED_GAPS[y] |= {"43101", "43102", "43103", "43104", "43105"}    # 熊本 구, 2013 승격
for y in range(2010, 2024):
    EXPECTED_GAPS[y] |= {"22138", "22139", "22140"}                      # 浜松 신 3구, 2024 개편

STR = {"muni_code": str, "muni_code_6digit": str, "muni": str, "city_code": str}
all_ = pd.concat(
    [pd.read_csv(f, dtype=STR) for f in sorted(glob.glob(os.path.join(SRC, "jp_pop_typed_*.csv")))],
    ignore_index=True,
)
all_["muni"] = all_.muni.fillna("")
POP = [c for c in all_.columns if c.startswith(("pop_", "age_"))]
assert len(POP) == 69
cmap = pd.read_csv(MAP, dtype=str).fillna("")
cmap = cmap[cmap.note != "pre2010_merger_chika_only"]  # 2010-01~03 합병: 인구 데이터에는 없고 지가공시(1/1)에만 있는 코드
cmap["last_year_old"] = cmap.last_year_old.astype(int)

# ---- 검사 1: 대응표가 데이터와 맞는가 ----
by_year = {y: g.set_index("muni_code") for y, g in all_.groupby("year")}
codes_2026 = set(by_year[2026].index)
for _, m in cmap.iterrows():
    y = m.last_year_old
    assert m.old_code in by_year[y].index, f"{m.old_code} not in {y}"
    assert by_year[y].muni[m.old_code] == m.old_name, f"{m.old_code} name {by_year[y].muni[m.old_code]} != {m.old_name}"
    if m.note == "E_rename":
        assert by_year[y + 1].muni[m.old_code] == m.new_name, m.old_code
    else:
        assert m.old_code not in by_year[y + 1].index, f"{m.old_code} still in {y + 1}"
    if m.new_code:
        assert m.new_code in codes_2026 and by_year[2026].muni[m.new_code] == m.new_name, m.new_code

# ---- 단위 행에 2026 코드·note 부여 ----
unit = all_[all_.row_type.isin(UNIT)].copy()
mp = cmap[cmap.new_code != ""].set_index("old_code")
hit = unit.muni_code.map(mp.last_year_old).notna() & (unit.year <= unit.muni_code.map(mp.last_year_old))
unit["std_code"] = unit.muni_code.where(~hit, unit.muni_code.map(mp.new_code))
unit["std_note"] = unit.muni_code.map(mp.note).where(hit, "")

# ---- 출력 3: C·D 행 분리 ----
excl = unit[unit.std_note.isin(EXCLUDE_NOTES)].drop(columns="std_code")
excl[POP] = excl[POP].astype("Int64")  # 2010~2014 NA 때문에 float로 저장되는 것 방지
keep = unit[~unit.std_note.isin(EXCLUDE_NOTES)]

# ---- 출력 1·2: 묶어 더하기 ----
g = keep.sort_values(["year", "std_code", "muni_code"]).groupby(["year", "std_code"], sort=True)
agg = g[POP].sum(min_count=1)
meta = g.agg(
    ref_date=("ref_date", "first"),
    orig_code=("muni_code", ";".join),
    orig_name=("muni", ";".join),
    n_orig=("muni_code", "size"),
    std_note=("std_note", lambda s: ";".join(sorted(set(x for x in s if x)))),
)
out = meta.join(agg).reset_index().rename(columns={"std_code": "muni_code"})
ref = by_year[2026].loc[by_year[2026].row_type.isin(UNIT), ["pref", "muni", "row_type", "city_code"]]
assert set(out.muni_code) <= set(ref.index), set(out.muni_code) - set(ref.index)
out = out.join(ref, on="muni_code")
head = ["year", "ref_date", "muni_code", "pref", "muni", "row_type", "city_code"]
std = ["std_note", "orig_code", "orig_name", "n_orig"]
out2 = out[head + std + POP].copy()
out1 = out[head + POP].copy()
for c in POP:
    out1[c] = out1[c].astype("Int64"); out2[c] = out2[c].astype("Int64")

# ---- 검사 ----
assert len(out1) == len(out2) and out1.equals(out2[head + POP])                                   # 2
assert not out1.duplicated(["year", "muni_code"]).any()                                           # 3
for y, s in out1.groupby("year").muni_code:                                                       # 4
    s = set(s); gap = EXPECTED_GAPS.get(y, set())
    assert s | gap == codes_2026 & set(ref.index) and not (s & gap), (y, s ^ (codes_2026 & set(ref.index)))
excl_city = excl.muni_code.map(mp.new_code)                                                       # 5
city_sets = {y: set(out1[out1.year == y].city_code) | set(excl_city[excl.year == y]) for y in range(2010, 2027)}
assert all(v == city_sets[2026] for v in city_sets.values()), {y: v ^ city_sets[2026] for y, v in city_sets.items() if v != city_sets[2026]}
for y in range(2010, 2027):                                                                       # 6
    pref_total = all_[(all_.year == y) & (all_.row_type == "pref")].pop_total.sum()
    assert out1[out1.year == y].pop_total.sum() + excl[excl.year == y].pop_total.sum() == pref_total, y
for c in ["03209", "09203", "11203", "23213", "32201", "32203"]:                                   # 7
    s = out1[out1.muni_code == c].sort_values("year").pop_total.astype(float)
    assert (s.pct_change().dropna().abs() < 0.10).all(), (c, s.pct_change().abs().max())
assert (out2.loc[out2.n_orig >= 2, "std_note"] == "B_merged_into").all()                          # 8
assert (out2.loc[out2.n_orig >= 2].apply(lambda r: r.orig_code.count(";") + 1 == r.n_orig, axis=1)).all()
assert len(excl) == 102 and excl.std_note.isin(EXCLUDE_NOTES).all(), len(excl)                    # 9

out1.to_csv(OUT1, index=False, encoding="utf-8-sig")
out2.to_csv(OUT2, index=False, encoding="utf-8-sig")
excl.to_csv(OUT3, index=False, encoding="utf-8-sig")
print("out1", out1.shape, "| out2", out2.shape, "| out3", excl.shape)
print(out1.groupby("year").size().to_string())
print(out2[out2.std_note != ""].std_note.value_counts().to_string())
