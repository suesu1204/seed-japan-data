"""비교표: 중앙값(v2) | 헤도닉A | 헤도닉B | A(1,000엔 하한 없음, 토지만만). 출력 chat_tables_hedonicB.md"""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); UP = os.path.join(HERE, "..", "1030_interm2")
B = pd.read_csv(os.path.join(HERE, "coefs_B.csv")).fillna({"ref": ""})
A = pd.read_csv(os.path.join(UP, "hedonic", "coefs_hedonic.csv")); Ar = pd.read_csv(os.path.join(UP, "hedonic", "coefs_hedonic_refcat.csv"))
M = pd.read_csv(os.path.join(UP, "coefs_v2_prefyear.csv")); Mr = pd.read_csv(os.path.join(UP, "coefs_refcat_v2.csv")); Mr = Mr[Mr.spec == "prefyearFE_sample"]
def st(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def fmt(r, term):
    d = 3 if term == "log_pop" else 4
    return f"{r.coef:.{d}f} ({r.se_cluster:.{d}f}){st(r.p)}".replace("-", "−")
def pick(df, **k):
    q = df
    for a, b in k.items(): q = q[q[a] == b]
    assert len(q) == 1, (k, len(q)); return q.iloc[0]
TERM = {"log_pop": "log_pop", "child_rate": "유소년", "youth_rate": "청년", "middle_rate": "중장년", "elderly_rate": "고령", "child_plus_elderly": "child+elderly", "child_minus_elderly": "child−elderly"}
MODEL = {"pop_only": "인구만", "aging_only": "고령화만", "both": "둘 다", "child": "유소년", "youth": "청년", "middle": "중장년", "elderly": "고령"}
L = ["# 헤도닉 사양 B 비교표 (1030_interm3)", "",
     "열: 중앙값(v2) | 헤도닉A (면적·용도지역·도로폭) | 헤도닉B (면적·건폐율·용적률, Saita 속성) | A(하한 없음) = 헤도닉A에서 1,000엔 미만 제외 규칙을 뺀 것(토지만만). 전부 시정촌 + 현×연도FE(장기차분 현×구간FE), 시정촌 군집. 칸 = 계수 (SE) 별표.", ""]
def cells(tab, ver, dep, model, term, ref=None):
    if ref is None:
        md = pick(M, table=tab, version=ver, dep=dep, model=model, term=term); a = pick(A, table=tab, version=ver, dep=dep, model=model, term=term)
        bm = model
    else:
        md = pick(Mr, version=ver, dep=dep, ref=ref, term=term); a = pick(Ar, version=ver, dep=dep, ref=ref, term=term); bm = "ref_" + ref
    b = pick(B, table=tab, version=ver, dep=dep + "_B", model=bm, term=term)
    out = [fmt(md, term), fmt(a, term), fmt(b, term)]; ns = [int(md.nobs), int(a.nobs), int(b.nobs)]
    if dep == "land":
        n = pick(B, table=tab, version=ver, dep="land_A_nofloor", model=bm, term=term); out.append(fmt(n, term)); ns.append(int(n.nobs))
    return out, ns
def head(dep, first):
    cols = ["중앙값(v2)", "헤도닉A", "헤도닉B"] + (["A(하한 없음)"] if dep == "land" else [])
    return "| " + first + " | " + " | ".join(cols) + " |", "|" + "---|" * (first.count("|") + 1 + len(cols))
VER = [("level", "수준 회귀"), ("ld5", "5년 장기차분")]; DEP = [("land", "토지만"), ("condo", "아파트")]
# H1
for ver, vn in VER:
    d = "Δ" if ver == "ld5" else ""
    for dep, dn in DEP:
        h1, h2 = head(dep, "열 | 항"); L += [f"## H1 — {vn}, {dn}", "", h1, h2]
        for model, terms in [("pop_only", ["log_pop"]), ("aging_only", ["elderly_rate"]), ("both", ["log_pop", "elderly_rate"])]:
            for t in terms:
                c, ns = cells("H1", ver, dep, model, t)
                L.append(f"| {MODEL[model]} | {d}{'log_pop' if t == 'log_pop' else 'elderly_rate'} | " + " | ".join(c) + " |")
        L.append("| nobs | | " + " | ".join(f"{x:,}" for x in ns) + " |"); L.append("")
# H2 (4 기준)
for ref, rn, lab in [("middle", "중장년", "H2"), ("child", "유소년", "H2(1)"), ("youth", "청년", "H2(2)"), ("elderly", "고령", "H2(3)")]:
    L += [f"## {lab} — 식: log 가격 = log_pop + 유소년 + 청년 + 고령 비중 ({rn} 기준)", ""]
    for ver, vn in VER:
        d = "Δ" if ver == "ld5" else ""
        for dep, dn in DEP:
            h1, h2 = head(dep, "항"); L += [f"**{vn}, {dn}**", "", h1, h2]
            for t in ["log_pop", "child_rate", "youth_rate", "middle_rate", "elderly_rate", "child_plus_elderly", "child_minus_elderly"]:
                if t == ref + "_rate": continue
                c, ns = cells("H2", ver, dep, "ref_" + ref, t, ref=ref)
                labt = TERM[t] if t in ("log_pop", "child_plus_elderly", "child_minus_elderly") else d + TERM[t]
                L.append(f"| {labt} | " + " | ".join(c) + " |")
            L.append("| nobs | " + " | ".join(f"{x:,}" for x in ns) + " |"); L.append("")
# H2-1
L += ["## H2-1 — 식: log 가격 = log_pop + 연령대 비중 하나 (모형 4개)", ""]
for ver, vn in VER:
    d = "Δ" if ver == "ld5" else ""
    for dep, dn in DEP:
        h1, h2 = head(dep, "모형 | 항"); L += [f"**{vn}, {dn}**", "", h1, h2]
        for m in ["child", "youth", "middle", "elderly"]:
            for t in [m + "_rate", "log_pop"]:
                c, ns = cells("H2-1", ver, dep, m, t)
                labt = (d + TERM[t] + (" 비중" if ver == "level" else "")) if t != "log_pop" else d + "log_pop"
                L.append(f"| {MODEL[m]} | {labt} | " + " | ".join(c) + " |")
        L.append("")
open(os.path.join(HERE, "chat_tables_hedonicB.md"), "w", encoding="utf-8").write("\n".join(L)); print(len(L), "lines")
