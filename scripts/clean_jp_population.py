"""1단계: Population2/ 17개 파일(住民基本台帳 市区町村別 年齢階級別 人口, 日本人住民, 2010~2026)을
같은 양식의 CSV 17개로 저장한다. 행 종류 정리·합병 처리·파생 변수는 하지 않는다(2~5단계).

입력: Population2/*.xls(x)
출력: output/population_clean/jp_pop_YYYY.csv
"""
import glob, os, re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Population2")
OUT = os.path.join(ROOT, "output", "population_clean")

AGE_LO = list(range(0, 100, 5)) + [100]            # 0,5,...,95,100
AGE_NAMES = [f"age_{a}_{a+4}" for a in AGE_LO[:-1]] + ["age_100p"]
POP_COLS = ["pop_total"] + AGE_NAMES + ["age_80p"]  # 23개
SEX = {"計": "", "男": "_m", "女": "_f"}


def parse_title(title):
    """'平成26年1月1日住民基本台帳…（日本人住民）' → (year, ref_date)."""
    m = re.match(r"(平成|令和)(\d+)年(\d+)月(\d+)日", title)
    year = (1988 if m.group(1) == "平成" else 2018) + int(m.group(2))
    return year, f"{year}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"


def load(path):
    d = pd.read_excel(path, header=None, dtype=str)
    title = str(d.iloc[0, 0])
    year, ref_date = parse_title(title)
    assert year < 2013 or "日本人住民" in title, f"{path}: 日本人住民 표기 없음"

    labels = d.iloc[1].tolist()                      # 연령 라벨은 모든 연도에서 2행째
    rows = d[d[0].str.fullmatch(r"\d{6}", na=False)]
    # 라벨에서 숫자만 뽑아 구간 하한으로 판별 ('5～9' / '5歳～9歳' / '80歳以上' 모두 처리)
    col_of = {}
    for c in range(5, d.shape[1]):
        lo = int(re.match(r"\d+", labels[c]).group())
        col_of[lo] = c
    has_80plus = col_of.get(80) is not None and "以上" in labels[col_of[80]]

    parts = []
    for sex, suf in SEX.items():
        r = rows[rows[3] == sex].set_index(0)
        num = r[list(range(4, d.shape[1]))].apply(pd.to_numeric, errors="coerce")
        p = pd.DataFrame(index=r.index)
        p["pop_total" + suf] = num[4]
        for lo, name in zip(AGE_LO, AGE_NAMES):
            c = col_of.get(lo)
            p[name + suf] = num[c] if c is not None and not (lo >= 80 and has_80plus) else pd.NA
        p["age_80p" + suf] = num[col_of[80]] if has_80plus else p[[n + suf for n in AGE_NAMES[16:]]].sum(axis=1)
        parts.append(p)
    wide = pd.concat(parts, axis=1).rename(columns={"pop_total_m": "pop_m", "pop_total_f": "pop_f"})

    base = rows[rows[3] == "計"].set_index(0)
    out = pd.DataFrame({
        "year": year,
        "ref_date": ref_date,
        "muni_code": base.index.str[:5],
        "muni_code_6digit": base.index,
        "pref": base[1].str.rstrip("*"),
        "muni": base[2].fillna("").str.rstrip("*").replace("-", ""),
    }, index=base.index)
    out = out.join(wide).reset_index(drop=True)
    for c in out.columns[6:]:
        out[c] = out[c].astype("Int64")
    return year, out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    years = {}
    for f in sorted(glob.glob(os.path.join(SRC, "*.xls*"))):
        year, df = load(f)
        assert year not in years, f"연도 중복: {year}"
        years[year] = df
        df.to_csv(os.path.join(OUT, f"jp_pop_{year}.csv"), index=False, encoding="utf-8-sig")

    # 자동 검사
    assert set(years) == set(range(2010, 2027)), sorted(years)
    for y, df in sorted(years.items()):
        assert list(df.columns) == ["year", "ref_date", "muni_code", "muni_code_6digit", "pref", "muni"] \
            + POP_COLS + ["pop_m"] + [c + "_m" for c in POP_COLS[1:]] + ["pop_f"] + [c + "_f" for c in POP_COLS[1:]]
        assert (df.pop_total == df.pop_m + df.pop_f).all(), y
        detail = df[AGE_NAMES[16:]]
        if y >= 2015:
            assert (detail.sum(axis=1) == df.age_80p).all(), y
        else:
            assert detail.isna().all().all(), y
        age_sum = df[AGE_NAMES[:16]].sum(axis=1) + df.age_80p
        rel = ((age_sum - df.pop_total).abs() / df.pop_total.replace(0, pd.NA)).dropna()
        print(f"{y}: rows={len(df):5d}  ref_date={df.ref_date[0]}  "
              f"age_sum≠pop_total rows={(rel > 0).sum():4d}  max rel diff={rel.max():.4%}")
    print("saved 17 files →", OUT)
