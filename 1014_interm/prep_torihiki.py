"""실거래가 전처리 (2026-10-14 임시 실행용).

입력: final_result2/torihiki.csv  (거래 건별, 전국, 2010Q1~2026Q1)
출력: 1014_interm/torihiki_median.csv        시정촌×연도 집계: 종류별 건수·㎡당 가격 중앙값 (결측 처리 전, 2010~2026)
      1014_interm/torihiki_preprocessed.csv  위에서 2010~2025만, 5건 미만은 결측, 로그 열 추가

규칙 (팀 결정 2026-10-14)
- 종류: 토지만(宅地(土地)) / 토지+건물(宅地(土地と建物)) 따로. 아파트·농지·임야는 제외
- ㎡당 가격 = trade_price ÷ area_sqm (거래별로 계산 후 중앙값)
- 5건 미만인 시정촌·연도·종류는 중앙값 결측
- 2026년은 1분기만 있어 제외
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = {"宅地(土地)": "land", "宅地(土地と建物)": "landbldg"}
MIN_N = 5

t = pd.read_csv(os.path.join(ROOT, "final_result2", "torihiki.csv"), dtype={"muni_code": str, "building_year": str})
t = t[t.type.isin(TYPES)].copy()
assert (t.area_sqm > 0).all() and (t.trade_price > 0).all()
t["ppsqm"] = t.trade_price / t.area_sqm
t["type"] = t.type.map(TYPES)

# 집계: 시정촌 × 연도 × 종류 → 건수, 중앙값 → 가로로 펼침
g = t.groupby(["year", "muni_code", "type"]).ppsqm.agg(n="size", med="median").reset_index()
wide = g.pivot(index=["year", "muni_code"], columns="type", values=["n", "med"])
wide.columns = [f"{a}_{b}" for a, b in wide.columns]
wide = wide.reset_index()
# 거래 없는 시정촌·연도도 행을 두기 위해 인구 패널의 (year, muni_code)에 맞춤
pop = pd.read_csv(os.path.join(ROOT, "final_result2", "jp_pop.csv"), dtype={"muni_code": str}, usecols=["year", "muni_code"])
out = pop.merge(wide, on=["year", "muni_code"], how="left")
for k in TYPES.values():
    out[f"n_{k}"] = out[f"n_{k}"].fillna(0).astype(int)
    out[f"med_{k}"] = out[f"med_{k}"].round(1)
out = out[["year", "muni_code", "n_land", "med_land", "n_landbldg", "med_landbldg"]]
assert len(out) == 1741 * 17 and out.n_land.sum() + out.n_landbldg.sum() == len(t)
out.to_csv(os.path.join(HERE, "torihiki_median.csv"), index=False, encoding="utf-8-sig")

# 전처리: 2010~2025, 5건 미만 결측, 로그
pre = out[out.year <= 2025].copy()
for k in TYPES.values():
    pre.loc[pre[f"n_{k}"] < MIN_N, f"med_{k}"] = np.nan
    pre[f"log_med_{k}"] = np.log(pre[f"med_{k}"])
pre.to_csv(os.path.join(HERE, "torihiki_preprocessed.csv"), index=False, encoding="utf-8-sig")

print("집계:", out.shape, "| 거래 사용:", len(t))
print("전처리:", pre.shape, f"| 5건 미만 결측 비율: land {pre.med_land.isna().mean():.1%}, landbldg {pre.med_landbldg.isna().mean():.1%}")
print(pre.describe().T[["count", "mean", "50%"]].round(2).to_string())
