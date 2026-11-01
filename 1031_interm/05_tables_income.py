"""소득 통제 비교표. 묶음 = 가격 측정(중앙값 v2 / 헤도닉A) × 버전(수준 / 5년 차분). 열 = 소득 없음/발표값/보간 × 토지·아파트 (2행 헤더). 출력 chat_tables_income.md"""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
C = pd.read_csv(os.path.join(HERE, "coefs_income.csv")).fillna({"ref": ""})
# 소득 없음 (2010~2025, 장기차분 3구간) = 기존 결과 그대로 가져옴. income = "full"
UP = os.path.join(HERE, "..")
def load(path, dep_map, **flt):
    d = pd.read_csv(os.path.join(UP, path))
    for a, b in flt.items(): d = d[d[a] == b]
    d = d[d.dep.isin(dep_map)].copy(); d["dep"] = d.dep.map(dep_map)
    if "model" not in d: d["model"] = "ref_" + d.ref
    return d[["table", "version", "dep", "model", "term", "coef", "se_cluster", "p", "nobs"]]
F = pd.concat([
    load("1030_interm2/coefs_v2_prefyear.csv", {"land": "land", "condo": "condo"}),
    load("1030_interm2/coefs_refcat_v2.csv", {"land": "land", "condo": "condo"}, spec="prefyearFE_sample").query("model != 'ref_middle'"),
    load("1030_interm3/coefs_B.csv", {"land_A_nofloor": "land_hedA_nofloor"}),
    load("1030_interm2/hedonic/coefs_hedonic.csv", {"condo": "condo_hedA"}),
    load("1030_interm2/hedonic/coefs_hedonic_refcat.csv", {"condo": "condo_hedA"}).query("model != 'ref_middle'"),
]); F["income"] = "full"; F["ref"] = ""
C = pd.concat([C, F], ignore_index=True)
def st(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def fmt(r, term):
    d = 3 if term in ("log_pop", "log_income_pc_raw", "log_income_pc_adj") else 4
    return f"{r.coef:.{d}f} ({r.se_cluster:.{d}f}){st(r.p)}".replace("-", "−")
def pick(**k):
    q = C
    for a, b in k.items(): q = q[q[a] == b]
    assert len(q) == 1, (k, len(q)); return q.iloc[0]
TERM = {"log_pop": "log_pop", "child_rate": "유소년", "youth_rate": "청년", "middle_rate": "중장년", "elderly_rate": "고령", "child_plus_elderly": "child+elderly", "child_minus_elderly": "child−elderly"}
MODEL = {"pop_only": "인구만", "aging_only": "고령화만", "both": "둘 다", "child": "유소년", "youth": "청년", "middle": "중장년", "elderly": "고령"}
MEAS = [("중앙값 v2", {"land": "land", "condo": "condo"}), ("헤도닉A (토지 = 하한 없음)", {"land": "land_hedA_nofloor", "condo": "condo_hedA"})]
VER = [("level", "수준 회귀"), ("ld5", "5년 장기차분")]
INC = ["full", "none", "raw", "adj"]; INC_T = {"raw": "log_income_pc_raw", "adj": "log_income_pc_adj"}
def head(first):
    k = first.count("|") + 1
    return ["| " + first + " | 소득 없음 (2010~25, 기존 결과) | | 소득 없음 (2010~24) | | 소득(발표값) | | 소득(보간) | |", "|" + "---|" * (k + 8),
            "| " + " | ".join([""] * k) + " | 토지 | 아파트 | 토지 | 아파트 | 토지 | 아파트 | 토지 | 아파트 |"]
def cells(deps, tab, ver, model, term):
    out = []
    for ic in INC:
        for side in ("land", "condo"):
            if term == "income": out.append("" if ic not in INC_T else fmt(pick(table=tab, version=ver, dep=deps[side], income=ic, model=model, term=INC_T[ic]), INC_T[ic]))
            else: out.append(fmt(pick(table=tab, version=ver, dep=deps[side], income=ic, model=model, term=term), term))
    return " | ".join(out)
def nobs(deps, tab, ver, model):
    return " | ".join(f"{int(pick(table=tab, version=ver, dep=deps[s], income=ic, model=model, term='log_pop').nobs):,}" for ic in INC for s in ("land", "condo"))
L = ["# 소득 통제 비교표 (1031_interm)", "",
     "소득 = log(1인당 課税対象所得), 1인당 = 課税対象所得 ÷ 所得割 납세의무자 수, 소득연도 기준(조사년도−1). 발표값 = 납세의무자 수 그대로, 보간 = 2024년도 조사(소득연도 2023)의 납세의무자 수만 2023·2025년도 평균으로 대체. 첫 열 소득 없음 (2010~25) = 기존 결과(1030_interm2·3) 그대로: 수준 2010~2025, 장기차분 3구간(2010→15, 15→20, 20→25). 나머지 세 열은 소득 있는 같은 표본: 수준 2010~2024, 장기차분 2구간(2010→15, 15→20). 장기차분은 끝점이 2010·2015·2020 이라 발표값·보간이 동일. 시정촌 + 현×연도FE(장기차분 현×구간FE), 시정촌 군집. 칸 = 계수 (SE) 별표.", ""]
for mn, deps in MEAS:
    for ver, vn in VER:
        d = "Δ" if ver == "ld5" else ""
        L += [f"# {mn} — {vn}", ""]
        L += ["## H1", ""] + head("열 | 항")
        for model, terms in [("pop_only", ["log_pop"]), ("aging_only", ["elderly_rate"]), ("both", ["log_pop", "elderly_rate"])]:
            for t in terms: L.append(f"| {MODEL[model]} | {d}{t} | " + cells(deps, "H1", ver, model, t) + " |")
            L.append(f"| {MODEL[model]} | {d}log 1인당 소득 | " + cells(deps, "H1", ver, model, "income") + " |")
        L.append("| nobs | | " + nobs(deps, "H1", ver, "both") + " |"); L.append("")
        for ref, rn, lab in [("middle", "중장년", "H2"), ("child", "유소년", "H2(1)"), ("youth", "청년", "H2(2)"), ("elderly", "고령", "H2(3)")]:
            L += [f"## {lab} — log 가격 = log_pop + 유소년 + 청년 + 고령 비중 ({rn} 기준) + log 1인당 소득", ""] + head("항")
            for t in ["log_pop", "child_rate", "youth_rate", "middle_rate", "elderly_rate", "child_plus_elderly", "child_minus_elderly"]:
                if t == ref + "_rate": continue
                labt = TERM[t] if t in ("log_pop", "child_plus_elderly", "child_minus_elderly") else d + TERM[t]
                L.append(f"| {labt} | " + cells(deps, "H2", ver, "ref_" + ref, t) + " |")
            L.append(f"| {d}log 1인당 소득 | " + cells(deps, "H2", ver, "ref_" + ref, "income") + " |")
            L.append("| nobs | " + nobs(deps, "H2", ver, "ref_" + ref) + " |"); L.append("")
        L += ["## H2-1 — log 가격 = log_pop + 연령대 비중 하나 + log 1인당 소득 (모형 4개)", ""] + head("모형 | 항")
        for m in ["child", "youth", "middle", "elderly"]:
            for t in [m + "_rate", "log_pop"]:
                labt = (d + TERM[t] + (" 비중" if ver == "level" else "")) if t != "log_pop" else d + "log_pop"
                L.append(f"| {MODEL[m]} | {labt} | " + cells(deps, "H2-1", ver, m, t) + " |")
            L.append(f"| {MODEL[m]} | {d}log 1인당 소득 | " + cells(deps, "H2-1", ver, m, "income") + " |")
        L.append("")
open(os.path.join(HERE, "chat_tables_income.md"), "w", encoding="utf-8").write("\n".join(L)); print(len(L), "lines")
