"""소득 2번. e-Stat(2010~2024년도) + 총무성 令和7年度(2025년도) 를 우리 1,741 시정촌 코드에 대응.
출력: income_panel.csv — muni_code, income_year(소득 발생 연도 = 조사년도−1), fy(조사년도), source, taxable_income_k(千円), n_taxpayers, income_pc_k(천 엔/인), log_income_pc
검증: 1,741 × 15년(2010~2024 소득연도) 전부 값 있는지, e-Stat 2024년도 → 총무성 2025년도 연속성
"""
import os, pandas as pd, numpy as np, openpyxl, warnings; warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ours = pd.read_csv(os.path.join(ROOT, "1030_interm2", "panel_v2.csv"), dtype={"muni_code": str}, usecols=["muni_code"]).muni_code.unique()
assert len(ours) == 1741

# ---- e-Stat ----
r = pd.read_csv(os.path.join(HERE, "income_raw.csv"), dtype=str, keep_default_na=False)
r["fy"] = r.year.str[:4].astype(int); r["v"] = pd.to_numeric(r.value, errors="coerce")
e = r[r.area_code.isin(ours) & r.fy.between(2011, 2024)].pivot_table(index=["area_code", "fy"], columns="item", values="v").reset_index()
e = e.rename(columns={"area_code": "muni_code", "C120110": "taxable_income_k", "C120120": "n_taxpayers"}); e["source"] = "e-Stat 0000020203"
assert len(e) == 1741 * 14 and e.taxable_income_k.notna().all() and e.n_taxpayers.notna().all(), "e-Stat 결측"

# ---- 총무성 令和7年度 第11表 (2025년도 = 2024년 소득) ----
ws = openpyxl.load_workbook(os.path.join(HERE, "raw", "J51-25-b.xlsx"), read_only=True, data_only=True).worksheets[0]
rows = [x for x in ws.iter_rows(values_only=True)]
hdr = rows[1]; assert hdr[1] == "団体コード" and hdr[4] == "表側" and hdr[5] == "所得割の納税義務者数" and hdr[13] == "課税対象所得", hdr
assert rows[3][5] == "人" and rows[3][13] == "千円", rows[3]
m = pd.DataFrame([x[:14] for x in rows[4:] if x and x[1] and x[4] == "市町村民税"], columns=list(hdr[:14]))
m["muni_code"] = m["団体コード"].astype(str).str[:5]
assert m.muni_code.is_unique, "총무성 표 코드 중복"
m = m[m.muni_code.isin(ours)]
assert len(m) == 1741, f"총무성 표 대응 {len(m)}/1741"
mic = pd.DataFrame({"muni_code": m.muni_code, "fy": 2025, "taxable_income_k": pd.to_numeric(m["課税対象所得"]), "n_taxpayers": pd.to_numeric(m["所得割の納税義務者数"]), "source": "総務省 R7 第11表 市町村別"})
assert mic.taxable_income_k.notna().all() and mic.n_taxpayers.notna().all()

# ---- 연속성 검증: 2025년도(총무성) vs 2024년도(e-Stat) ----
chk = e[e.fy == 2024][["muni_code", "taxable_income_k", "n_taxpayers"]].merge(mic[["muni_code", "taxable_income_k", "n_taxpayers"]], on="muni_code", suffixes=("_24", "_25"))
g_inc = chk.taxable_income_k_25 / chk.taxable_income_k_24; g_n = chk.n_taxpayers_25 / chk.n_taxpayers_24
prev = e[e.fy.isin([2023, 2024])].pivot(index="muni_code", columns="fy", values="taxable_income_k"); g_prev = prev[2024] / prev[2023]
print("2025/2024 課税対象所得 비율: 중앙값", round(g_inc.median(), 4), "p1", round(g_inc.quantile(.01), 3), "p99", round(g_inc.quantile(.99), 3), "| 참고 2024/2023(e-Stat 내부):", round(g_prev.median(), 4), round(g_prev.quantile(.01), 3), round(g_prev.quantile(.99), 3))
print("2025/2024 납세의무자 비율: 중앙값", round(g_n.median(), 4), "p1", round(g_n.quantile(.01), 3), "p99", round(g_n.quantile(.99), 3))
print("비율 0.8 미만 또는 1.25 초과 시정촌:", int(((g_inc < .8) | (g_inc > 1.25)).sum()))

# ---- 합치기 ----
out = pd.concat([e, mic], ignore_index=True)
out["income_year"] = out.fy - 1
out["income_pc_k"] = out.taxable_income_k / out.n_taxpayers
out["log_income_pc"] = np.log(out.income_pc_k)
out = out[["muni_code", "income_year", "fy", "source", "taxable_income_k", "n_taxpayers", "income_pc_k", "log_income_pc"]].sort_values(["muni_code", "income_year"])
assert len(out) == 1741 * 15 and out.income_year.min() == 2010 and out.income_year.max() == 2024 and not out.duplicated(["muni_code", "income_year"]).any()
out.to_csv(os.path.join(HERE, "income_panel.csv"), index=False, encoding="utf-8-sig", float_format="%.6f")
print("income_panel.csv", out.shape, "| 소득연도 2010~2024, 1,741곳 전부 | 1인당(천엔) 중앙값", round(out.income_pc_k.median(), 1))
