"""panel_v4.csv = 1030_interm3/panel_v3.csv (39열) + 소득 열. 기존 열은 손대지 않음.
소득 열 (소득연도 = 패널 year 로 붙임; 조사년도 = year+1):
  taxable_income_k  課税対象所得 합계(千円)
  n_taxpayers_raw   납세의무자 수 (발표값)
  n_taxpayers_adj   납세의무자 수 (2024년도 조사 = 소득연도 2023 만 2023·2025년도 평균으로 보간, 나머지 동일)
  income_pc_raw, log_income_pc_raw   1인당 (발표값 분모)
  income_pc_adj, log_income_pc_adj   1인당 (보간 분모)
  2025년 행은 소득 결측 (2026년도 조사 미공표)
"""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
p = pd.read_csv(os.path.join(ROOT, "1030_interm3", "panel_v3.csv"), dtype={"muni_code": str, "pref_code": str})
inc = pd.read_csv(os.path.join(HERE, "income_panel.csv"), dtype={"muni_code": str})
w = inc.pivot(index="muni_code", columns="fy", values="n_taxpayers")
adj = inc.set_index(["muni_code", "fy"]).n_taxpayers.copy()
interp = (w[2023] + w[2025]) / 2
for mc, v in interp.items(): adj.loc[(mc, 2024)] = v
inc = inc.merge(adj.rename("n_taxpayers_adj").reset_index(), on=["muni_code", "fy"])
inc = inc.rename(columns={"n_taxpayers": "n_taxpayers_raw", "income_pc_k": "income_pc_raw", "log_income_pc": "log_income_pc_raw"})
inc["income_pc_adj"] = inc.taxable_income_k / inc.n_taxpayers_adj; inc["log_income_pc_adj"] = np.log(inc.income_pc_adj)
keep = ["muni_code", "income_year", "taxable_income_k", "n_taxpayers_raw", "n_taxpayers_adj", "income_pc_raw", "log_income_pc_raw", "income_pc_adj", "log_income_pc_adj"]
out = p.merge(inc[keep].rename(columns={"income_year": "year"}), on=["muni_code", "year"], how="left")
assert len(out) == 27856 and list(out.columns[:39]) == list(p.columns) and all(out[c].equals(p[c]) for c in p.columns)
assert out[out.year <= 2024].log_income_pc_raw.notna().all() and out[out.year == 2025].log_income_pc_raw.isna().all()
chg = (out.n_taxpayers_adj / out.n_taxpayers_raw)[out.year == 2023]
print("보간 비율(2023 소득연도, adj/raw): 중앙값", round(chg.median(), 4), "p1", round(chg.quantile(.01), 3), "p99", round(chg.quantile(.99), 3))
out.to_csv(os.path.join(HERE, "panel_v4.csv"), index=False, encoding="utf-8-sig", float_format="%.6f")
print("panel_v4.csv", out.shape, "| 기존 39열 동일 확인 | log_income_pc_raw 요약:", out.log_income_pc_raw.describe()[["count", "mean", "min", "max"]].round(3).to_dict())
