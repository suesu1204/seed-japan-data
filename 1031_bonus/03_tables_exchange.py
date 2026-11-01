"""교환 효과 전체표: 연령층 A 1%p ↓, B 1%p ↑ 일 때 log 가격 변화 (= A 기준 회귀에서 B 비중의 계수). 새 회귀 없음.
구성: 연령층 A마다 'A ↓ (A → ?)' 표와 'A ↑ (? → A)' 표. 행 = 상대 연령층 × 소득 사양 3, 열 = 수준·장기차분 × (중앙값 토지·아파트, 헤도닉A 토지·아파트).
출처: 기준 범주 4종 결과. 소득 없음(2010~25) = 1030_interm2·3, 소득 없음(2010~24)·소득(보간) = 1031_interm/coefs_income.csv. 출력 chat_tables_exchange.md"""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); UP = os.path.join(HERE, "..")
def rd(p): return pd.read_csv(os.path.join(UP, p))
K = ["version", "dep", "ref", "term", "coef", "se_cluster", "p", "nobs"]
F = []
r = rd("1030_interm2/coefs_refcat_v2.csv"); F.append(r[r.spec == "prefyearFE_sample"][K])
h = rd("1030_interm2/hedonic/coefs_hedonic_refcat.csv"); F.append(h[h.dep == "condo"].assign(dep="condo_hedA")[K])
b = rd("1030_interm3/coefs_B.csv"); b = b[(b.dep == "land_A_nofloor") & (b.table == "H2")].assign(dep="land_hedA"); F.append(b[K])
full = pd.concat(F).assign(spec="full")
inc = rd("1031_interm/coefs_income.csv"); inc = inc[(inc.table == "H2") & inc.income.isin(["none", "adj"]) & inc.dep.isin(["land", "condo", "land_hedA_nofloor", "condo_hedA"])].copy()
inc["ref"] = inc.model.str.replace("ref_", ""); inc["dep"] = inc.dep.replace({"land_hedA_nofloor": "land_hedA"}); inc["spec"] = inc.income.map({"none": "none24", "adj": "adj"})
C = pd.concat([full, inc[K + ["spec"]]], ignore_index=True)
def st(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def cell(q, sign=1):
    assert len(q) == 1, len(q); x = q.iloc[0]
    return f"{sign*x.coef:.4f} ({x.se_cluster:.4f}){st(x.p)}".replace("-", "−")
N = {"child": "유소년", "youth": "청년", "middle": "중장년", "elderly": "고령"}
DEPS = ["land", "condo", "land_hedA", "condo_hedA"]
SPECS = [("full", "소득 없음 (10~25)"), ("none24", "소득 없음 (10~24)"), ("adj", "소득 보간 (10~24)")]
HEAD = ["| 상대 | 소득 | 수준 회귀 | | | | 5년 장기차분 | | | |", "|---" * 10 + "|",
        "| | | 중앙값 토지 | 중앙값 아파트 | 헤도닉 토지 | 헤도닉 아파트 | 중앙값 토지 | 중앙값 아파트 | 헤도닉 토지 | 헤도닉 아파트 |"]
L = ["# 연령층 교환 효과 전체표 (1031_bonus)", "",
     "칸 = A 비중 1%p ↓, B 비중 1%p ↑ (나머지 그대로)일 때 log 가격 변화, 계수 (SE) 별표. A 기준 회귀에서 B 비중의 계수. 'A ↑' 표는 같은 값의 부호를 뒤집은 것.",
     "소득 없음 (10~25) = 기존 결과(장기차분 3구간). 소득 없음 (10~24)·소득 보간 = 소득 있는 표본(장기차분 2구간). 헤도닉 토지 = 사양 A 하한 없음. 시정촌 + 현×연도FE(차분 현×구간FE), 시정촌 군집.",
     "H3(교환 정의) = '유소년 ↓' 표의 고령 행. H3(크기 비교 정의)는 이 표에 없음(chat_tables_income.md의 child+elderly 행).", ""]
def rows(a, down):
    out = []
    for b_ in [g for g in N if g != a]:
        for i, (sp, sn) in enumerate(SPECS):
            cells = []
            for ver in ["level", "ld5"]:
                for dep in DEPS:
                    q = C[(C.spec == sp) & (C.version == ver) & (C.dep == dep)]
                    # A↓B↑ = ref a, term b ; A↑B↓ = −(ref a, term b)
                    cells.append(cell(q[(q.ref == a) & (q.term == b_ + "_rate")], 1 if down else -1))
            lab = (f"{N[a]} → {N[b_]}" if down else f"{N[b_]} → {N[a]}") if i == 0 else ""
            out.append(f"| {lab} | {sn} | " + " | ".join(cells) + " |")
    return out
for a in N:
    L += [f"## {N[a]} ↓ ({N[a]} → ?)", ""] + HEAD + rows(a, True) + [""]
    L += [f"## {N[a]} ↑ (? → {N[a]})", ""] + HEAD + rows(a, False) + [""]
nb = {(sp, ver, dep): int(C[(C.spec == sp) & (C.version == ver) & (C.dep == dep) & (C.ref == "middle") & (C.term == "log_pop")].iloc[0].nobs) for sp, _ in SPECS for ver in ["level", "ld5"] for dep in DEPS}
L += ["## nobs", "", "| 소득 | 중앙값 토지 | 중앙값 아파트 | 헤도닉 토지 | 헤도닉 아파트 | 중앙값 토지 | 중앙값 아파트 | 헤도닉 토지 | 헤도닉 아파트 |", "|---" * 9 + "|"]
for sp, sn in SPECS: L.append(f"| {sn} | " + " | ".join(f"{nb[(sp, ver, dep)]:,}" for ver in ["level", "ld5"] for dep in DEPS) + " |")
open(os.path.join(HERE, "chat_tables_exchange.md"), "w", encoding="utf-8").write("\n".join(L)); print(len(L), "lines")
