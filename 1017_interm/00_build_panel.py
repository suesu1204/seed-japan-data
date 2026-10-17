"""0단계. panel.csv 생성 (계획서 0단계 그대로).

입력 (final_result2/)
  jp_pop_detail.csv : year, muni_code, pop_total, age_0_4 ... age_75_79, age_80p
  torihiki.csv      : year, muni_code, type, trade_price, area_sqm   (거래 건별)
  chika.csv         : year, muni_code, n_residential, med_residential
  muni_names.csv    : muni_code, kaso
출력 (1017_interm/)
  panel.csv : 행 = 시정촌 × 연도 (1,741 × 2010~2025 = 27,856)
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "final_result2")
YEARS = list(range(2010, 2026))
MIN_N = 5
TYPES = {"宅地(土地)": "land", "宅地(土地と建物)": "landbldg", "中古マンション等": "condo"}
AGE = ["age_0_4", "age_5_9", "age_10_14", "age_15_19", "age_20_24", "age_25_29", "age_30_34",
       "age_35_39", "age_40_44", "age_45_49", "age_50_54", "age_55_59", "age_60_64",
       "age_65_69", "age_70_74", "age_75_79", "age_80p"]


def need(df, cols, name):
    miss = [c for c in cols if c not in df.columns]
    assert not miss, f"{name}: 없는 열 {miss}"


# ---------- 인구 ----------
pop = pd.read_csv(os.path.join(SRC, "jp_pop_detail.csv"), dtype={"muni_code": str})
need(pop, ["year", "muni_code", "pop_total"] + AGE, "jp_pop_detail")
pop = pop[pop.year.isin(YEARS)].copy()
assert len(pop) == 1741 * len(YEARS) and pop[AGE].isna().sum().sum() == 0
# 원본에서 78행은 연령별 합계가 총인구보다 1~6명 작음(연령 불명자가 총인구에만 포함). 분모는 총인구 그대로 사용.
gap = pop.pop_total - pop[AGE].sum(axis=1)
assert gap.between(0, 10).all(), f"연령 합계와 총인구 차이 범위 이상: {gap.min()}~{gap.max()}"

p = pop[["year", "muni_code", "pop_total"]].copy()
p["pref_code"] = p.muni_code.str[:2]
p["log_pop"] = np.log(pop.pop_total)
pct = lambda cols: pop[cols].sum(axis=1) / pop.pop_total * 100
p["child_rate"] = pct(AGE[0:3])        # 0-14
p["youth_rate"] = pct(AGE[3:7])        # 15-34
p["middle_rate"] = pct(AGE[7:13])      # 35-64
p["elderly_rate"] = pct(AGE[13:17])    # 65+
p["aging_rate"] = p.elderly_rate
p["share_15_19"] = pct(AGE[3:4])       # 민감도: 청년 20-34 로 바꿀 때 분리
p["share_20_34"] = pct(AGE[4:7])
p["share_65_74"] = pct(AGE[13:15])     # 민감도: 75세 이상 분리
p["share_75p"] = pct(AGE[15:17])
chk = p.child_rate + p.youth_rate + p.middle_rate + p.elderly_rate
assert chk.between(99.9, 100 + 1e-6).all(), "비중 합이 100 에서 벗어남"

# 규모 그룹 (2010년 인구)
pop2010 = p[p.year == 2010].set_index("muni_code").pop_total
p["pop2010"] = p.muni_code.map(pop2010)
p["size_group"] = pd.cut(p.pop2010, [0, 10_000, 50_000, 200_000, np.inf], labels=[1, 2, 3, 4], right=False).astype(int)

# 과소 더미
names = pd.read_csv(os.path.join(SRC, "muni_names.csv"), dtype={"muni_code": str})
need(names, ["muni_code", "kaso"], "muni_names")
p["kaso_dummy"] = p.muni_code.map(names.set_index("muni_code").kaso).isin(["全部過疎", "みなし過疎"]).astype(int)
assert p.kaso_dummy.sum() == 727 * len(YEARS)

# ---------- 실거래 ----------
t = pd.read_csv(os.path.join(SRC, "torihiki.csv"), dtype={"muni_code": str, "building_year": str},
                usecols=["year", "muni_code", "type", "trade_price", "area_sqm"])
need(t, ["year", "muni_code", "type", "trade_price", "area_sqm"], "torihiki")
t = t[t.year.isin(YEARS) & t.type.isin(TYPES)].copy()
assert (t.area_sqm > 0).all() and (t.trade_price > 0).all()
t["ppsqm"] = t.trade_price / t.area_sqm
t["type"] = t.type.map(TYPES)
g = t.groupby(["year", "muni_code", "type"]).ppsqm.agg(n="size", med="median").reset_index()
w = g.pivot(index=["year", "muni_code"], columns="type", values=["n", "med"])
w.columns = [f"{a}_{b}" for a, b in w.columns]
w = w.reset_index()
p = p.merge(w, on=["year", "muni_code"], how="left")
for k in TYPES.values():
    p[f"n_{k}"] = p[f"n_{k}"].fillna(0).astype(int)
    p[f"log_p_{k}"] = np.log(p[f"med_{k}"].where(p[f"n_{k}"] >= MIN_N))
    p = p.drop(columns=f"med_{k}")
assert sum(p[f"n_{k}"].sum() for k in TYPES.values()) == len(t)

# ---------- 공시지가 ----------
c = pd.read_csv(os.path.join(SRC, "chika.csv"), dtype={"muni_code": str}, usecols=["year", "muni_code", "n_residential", "med_residential"])
need(c, ["year", "muni_code", "n_residential", "med_residential"], "chika")
p = p.merge(c.rename(columns={"n_residential": "n_chika"}), on=["year", "muni_code"], how="left")
p["n_chika"] = p.n_chika.fillna(0).astype(int)
p["log_p_chika"] = np.log(p.med_residential.where(p.n_chika > 0))
p = p.drop(columns="med_residential")

# ---------- 장기차분용 끝점 3년 평균 ----------
# 끝점 y 의 3년 평균: 2015·2020 은 y-1..y+1, 2010 은 2010..2012, 2025 는 2023..2025. 값 있는 해만 평균.
p = p.sort_values(["muni_code", "year"]).reset_index(drop=True)
AVG_COLS = ["log_p_land", "log_p_landbldg", "log_p_condo", "log_p_chika", "log_pop",
            "child_rate", "youth_rate", "middle_rate", "elderly_rate", "share_15_19", "share_20_34", "share_65_74", "share_75p"]
win = {2010: [2010, 2011, 2012], 2015: [2014, 2015, 2016], 2020: [2019, 2020, 2021], 2025: [2023, 2024, 2025]}
for col in AVG_COLS:
    p[f"avg3_{col}"] = np.nan
    for y, ys in win.items():
        m = p[p.year.isin(ys)].groupby("muni_code")[col].mean()
        idx = p.year == y
        p.loc[idx, f"avg3_{col}"] = p.loc[idx, "muni_code"].map(m).values

# ---------- 출력 ----------
order = (["muni_code", "year", "pref_code",
          "n_land", "log_p_land", "n_landbldg", "log_p_landbldg", "n_condo", "log_p_condo", "n_chika", "log_p_chika",
          "pop_total", "log_pop", "child_rate", "youth_rate", "middle_rate", "elderly_rate", "aging_rate",
          "share_15_19", "share_20_34", "share_65_74", "share_75p",
          "pop2010", "size_group", "kaso_dummy"] + [f"avg3_{c}" for c in AVG_COLS])
p = p[order]
assert p.shape == (1741 * len(YEARS), len(order)) and not p.duplicated(["muni_code", "year"]).any()
p.to_csv(os.path.join(HERE, "panel.csv"), index=False, encoding="utf-8-sig", float_format="%.6f")

print("panel.csv", p.shape)
print("거래 사용:", len(t), "| 종류별:", t.type.value_counts().to_dict())
print("가격 결측 비율:", {k: round(p[f"log_p_{k}"].isna().mean(), 3) for k in list(TYPES.values()) + ["chika"]})
print("규모 그룹별 시정촌 수:", p[p.year == 2010].size_group.value_counts().sort_index().to_dict())
print("과소 시정촌 수:", int(p[p.year == 2010].kaso_dummy.sum()))
