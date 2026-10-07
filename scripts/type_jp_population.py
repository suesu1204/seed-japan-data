"""2단계: 1단계 CSV 17개의 모든 행을 그대로 두고 row_type, city_code 컬럼을 추가한다.
행은 하나도 지우지 않는다. 어느 단위로 거를지는 분석 때 row_type으로 고른다.

입력: output/population_clean/jp_pop_YYYY.csv
출력: output/population_typed/jp_pop_typed_YYYY.csv
"""
import glob, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "output", "population_clean")
OUT = os.path.join(ROOT, "output", "population_typed")

UNIT = ["ward", "special_ward", "city", "town", "village"]  # 시구정촌 분석 단위


def row_type(r):
    """코드 3~5자리 범위 + 이름 끝글자로 판별. 코드만으로는 안 됨(README 4.1 참고)."""
    m3, name, pref = r.muni_code[2:], r.muni, r.muni_code[:2]
    if r.pop_total == 0:
        return "zero_pop"
    if m3 == "000":
        return "pref"
    if m3 < "200":
        return "city_agg" if name.endswith("市") else ("special_ward" if pref == "13" else "ward")
    if m3 < "300":
        return "city"
    if name.endswith("郡"):
        return "gun_agg"
    if name == "島しょ":
        return "island_agg"
    if name.endswith("町"):
        return "town"
    if name.endswith("村"):
        return "village"
    raise ValueError(f"판별 불가: {r.muni_code} {name}")


def add_types(df):
    df = df.copy()
    df["muni"] = df.muni.fillna("")
    df["row_type"] = df.apply(row_type, axis=1)
    # city_code: ward는 소속 정령시 합계 코드, 단위 행은 자기 코드, 합계 행은 빈칸
    agg = df[df.row_type == "city_agg"]
    city_of_ward = {}
    for _, a in agg.iterrows():
        wards = df[(df.row_type == "ward") & df.muni.str.startswith(a.muni) & (df.muni_code.str[:2] == a.muni_code[:2])]
        city_of_ward.update(dict.fromkeys(wards.muni_code, a.muni_code))
    df["city_code"] = df.muni_code.where(df.row_type.isin(UNIT))
    df.loc[df.row_type == "ward", "city_code"] = df.muni_code.map(city_of_ward)
    cols = list(df.columns)
    i = cols.index("muni") + 1
    return df[cols[:i] + ["row_type", "city_code"] + [c for c in cols[i:] if c not in ("row_type", "city_code")]]


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    summary = {}
    for f in sorted(glob.glob(os.path.join(SRC, "jp_pop_*.csv"))):
        src = pd.read_csv(f, dtype={"muni_code": str, "muni_code_6digit": str, "muni": str})
        df = add_types(src)
        year = int(df.year[0])
        df.to_csv(os.path.join(OUT, f"jp_pop_typed_{year}.csv"), index=False, encoding="utf-8-sig")

        # 검사
        assert len(df) == len(src) and df.shape[1] == 77, (year, df.shape)
        assert not df.muni_code.duplicated().any(), year
        assert df.loc[df.row_type == "ward", "city_code"].notna().all(), year
        unit = df[df.row_type.isin(UNIT)]
        for p, g in df.groupby(df.muni_code.str[:2]):
            assert g[g.row_type == "pref"].pop_total.sum() == g[g.row_type.isin(UNIT)].pop_total.sum(), (year, p)
        for _, a in df[df.row_type == "city_agg"].iterrows():
            assert unit[unit.city_code == a.muni_code].pop_total.sum() == a.pop_total, (year, a.muni)
        summary[year] = df.row_type.value_counts()
    tab = pd.DataFrame(summary).T.fillna(0).astype(int)
    assert list(tab.index) == list(range(2010, 2027))
    print(tab.to_string())
    print("saved 17 files →", OUT)
