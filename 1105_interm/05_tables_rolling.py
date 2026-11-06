"""coefs_rolling.csv + coefs.csv → results_rolling.md (이동 5년 차분, 비중첩 3구간 차분과 나란히)."""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
r = pd.read_csv(os.path.join(HERE, "coefs_rolling.csv")); c = pd.read_csv(os.path.join(HERE, "coefs.csv")); c = c[(c.version == "ld5") & (c.fe == "year")]
def cell(x):
    s = "***" if x.p < .01 else "**" if x.p < .05 else "*" if x.p < .1 else ""
    d = 3 if x.term in ("log_pop", "log_income_pc_adj") else 4
    return f"{x.coef:.{d}f} ({x.se_cluster:.{d}f}){s}".replace("-", "−")
ROWS = [("H1", "pop_only", "log_pop", "H1 인구만: Δlog_pop"), ("H1", "aging_only", "elderly_rate", "H1 고령화만: Δ고령"),
        ("H1", "both", "log_pop", "H1 둘 다: Δlog_pop"), ("H1", "both", "elderly_rate", "H1 둘 다: Δ고령"),
        ("H3", "ref_middle", "log_pop", "H3: Δlog_pop"), ("H3", "ref_middle", "child_rate", "H3: Δ유소년"), ("H3", "ref_middle", "youth_rate", "H3: Δ청년"),
        ("H3", "ref_middle", "elderly_rate", "H3: Δ고령"), ("H3", "ref_middle", "log_income_pc_adj", "H3: Δlog 소득")]
DEPN = {"house": "단독주택", "condo": "아파트", "resi": "단독+아파트", "land": "토지"}
md = ["# 5년 이동차분 (2026-11-05)\n", "구간 = t−5 → t. 이동 = t 2015~2025(소득 통제: 2015~2024, 10구간), 종료연도 고정효과. 비중첩 = 2010→15, 15→20, 20→25(소득 통제: 앞 2구간), 구간 고정효과. SE 시정촌 군집. 종속변수·설명변수 정의는 results.md 와 동일.\n"]
for inc, incn in [("no", "소득 통제 없음"), ("yes", "소득 통제")]:
    md.append(f"## {incn}\n")
    deps = ["house", "condo", "resi", "land"]
    md.append("| 항 | " + " | ".join(f"{DEPN[d]} 이동" for d in deps) + " | " + " | ".join(f"{DEPN[d]} 비중첩" for d in deps if d != "land") + " |"); md.append("|---" * (2 * len(deps)) + "|")
    for tab, model, term, label in ROWS:
        if term == "log_income_pc_adj" and inc == "no": continue
        vals = []
        for d in deps:
            x = r[(r.income == inc) & (r.table == tab) & (r.model == model) & (r.term == term) & (r.dep == d)]; vals.append(cell(x.iloc[0]) if len(x) else "")
        for d in deps:
            if d == "land": continue
            x = c[(c.income == inc) & (c.table == tab) & (c.model == model) & (c.term == term) & (c.dep == d)]; vals.append(cell(x.iloc[0]) if len(x) else "")
        md.append(f"| {label} | " + " | ".join(vals) + " |")
    n1 = [f"{int(r[(r.income == inc) & (r.table == 'H3') & (r.dep == d)].nobs.iloc[0]):,}" for d in deps]
    n2 = [f"{int(c[(c.income == inc) & (c.table == 'H3') & (c.dep == d)].nobs.iloc[0]):,}" for d in deps if d != "land"]
    md.append("| nobs | " + " | ".join(n1 + n2) + " |\n")
open(os.path.join(HERE, "results_rolling.md"), "w", encoding="utf-8").write("\n".join(md)); print("results_rolling.md")
