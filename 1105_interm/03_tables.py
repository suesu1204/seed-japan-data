"""1105_interm 4단계: coefs.csv → results.md (단독주택 vs 아파트 표)."""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
c = pd.read_csv(os.path.join(HERE, "coefs.csv"))
def cell(r):
    s = "***" if r.p < .01 else "**" if r.p < .05 else "*" if r.p < .1 else ""
    d = 3 if r.term.endswith("log_pop") or r.term == "log_income_pc_adj" else 4
    return f"{r.coef:.{d}f} ({r.se_cluster:.{d}f}){s}".replace("-", "−")
ROWS = [("H1", "pop_only", "log_pop", "H1 인구만: log_pop"), ("H1", "aging_only", "elderly_rate", "H1 고령화만: 고령"),
        ("H1", "both", "log_pop", "H1 둘 다: log_pop"), ("H1", "both", "elderly_rate", "H1 둘 다: 고령"),
        ("H3", "ref_middle", "log_pop", "H3: log_pop"), ("H3", "ref_middle", "child_rate", "H3: 유소년"),
        ("H3", "ref_middle", "youth_rate", "H3: 청년"), ("H3", "ref_middle", "elderly_rate", "H3: 고령"), ("H3", "ref_middle", "log_income_pc_adj", "H3: log 소득")]
DEPN = {"house": "단독주택", "condo": "아파트", "resi": "단독주택+아파트"}
FEN = {"year": "지역+연도", "prefyear": "지역+현×연도"}
md = ["# 거주용 단독주택 vs 아파트 (2026-11-05)\n",
      "단독주택 = 宅地(土地と建物) 중 Use=住宅, 가격 = 거래총액 ÷ 건물 연면적. 아파트 = 中古マンション等, 전용면적당. 단독주택+아파트 = 두 거래를 한 풀로 묶은 중앙값. 시정촌·연도 중앙값 log, 5건 미만 결측. 고정효과 = 시정촌 + 연도(차분: 구간).",
      "소득 통제 = log 1인당 과세대상소득(보간), 표본 2010~2024(차분 2010→15, 15→20). 소득 없음 = 2010~2025(차분 3구간). 칸 = 계수 (SE, 시정촌 군집). *** 1%, ** 5%, * 10%.\n"]
for inc, incn in [("no", "소득 통제 없음"), ("yes", "소득 통제")]:
    for ver, vern in [("level", "수준 회귀"), ("ld5", "5년 장기차분")]:
        sub = c[(c.income == inc) & (c.version == ver)]
        cols = [(d, "year") for d in ["house", "condo", "resi"]]
        md.append(f"## {incn} · {vern}\n")
        md.append("| 항 | " + " | ".join(DEPN[d] for d, fe in cols) + " |"); md.append("|---" * (len(cols) + 1) + "|")
        for tab, model, term, label in ROWS:
            if term == "log_income_pc_adj" and inc == "no": continue
            vals = []
            for d, fe in cols:
                r = sub[(sub.table == tab) & (sub.model == model) & (sub.term == term) & (sub.dep == d) & (sub.fe == fe)]
                vals.append(cell(r.iloc[0]) if len(r) else "")
            md.append(f"| {label} | " + " | ".join(vals) + " |")
        nobs = [str(int(sub[(sub.table == "H3") & (sub.dep == d) & (sub.fe == fe)].nobs.iloc[0])) for d, fe in cols]
        md.append("| nobs | " + " | ".join(f"{int(n):,}" for n in nobs) + " |\n")
open(os.path.join(HERE, "results.md"), "w", encoding="utf-8").write("\n".join(md)); print("results.md")
