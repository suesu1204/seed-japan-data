"""1절 표(H1·H2 × 수준/차분)의 소득 통제판. 헤더 2행 = 지역+연도+소득 / 지역+현×연도+소득. 출력 table_fe_income.md, .html"""
import os, re, html, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
C = pd.read_csv(os.path.join(HERE, "coefs_summary_income.csv"))
def st(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def pick(**k):
    q = C
    for a, b in k.items(): q = q[q[a] == b]
    assert len(q) == 1, (k, len(q)); return q.iloc[0]
def fmt(x, term): d = 3 if term in ("log_pop", "log_income_pc_adj") else 4; return f"{x.coef:.{d}f} ({x.se_cluster:.{d}f}){st(x.p)}".replace("-", "−")
DEPS = [("land", "중앙값 토지"), ("condo", "중앙값 아파트"), ("land_hedA", "헤도닉 토지"), ("condo_hedA", "헤도닉 아파트")]
FES = [("year", "지역+연도+소득"), ("prefyear", "지역+현×연도+소득")]
L = ["## 소득 통제판 (log 1인당 課税対象所得 추가)", "",
     "소득 = log(課税対象所得 ÷ 所得割 납세의무자 수), 소득연도 기준(조사년도−1), 2024년도 납세의무자 수는 전후 연도 평균으로 보간. 소득이 있는 2010~2024만 사용(2025 제외). 5년 장기차분은 2010→15, 15→20 두 구간. 나머지 사양은 1절과 같음.", ""]
def head2(first):
    k = first.count("|") + 1
    return ["| " + first + " | " + " | ".join(f"{dn} | " for _, dn in DEPS) + "|", "|" + "---|" * (k + 8),
            "| " + " | ".join([""] * k) + " | " + " | ".join(" | ".join(fn for _, fn in FES) for _ in DEPS) + " |"]
for ver, vn in [("level", "수준 회귀"), ("ld5", "5년 장기차분")]:
    d = "Δ" if ver == "ld5" else ""
    L += [f"### {vn}", ""] + head2("모형 | 항")
    for model, mn, terms in [("pop_only", "H1 인구만", ["log_pop", "log_income_pc_adj"]), ("aging_only", "H1 고령화만", ["elderly_rate", "log_income_pc_adj"]), ("both", "H1 둘 다", ["log_pop", "elderly_rate", "log_income_pc_adj"]),
                             ("ref_middle", "H2 (중장년 기준)", ["log_pop", "child_rate", "youth_rate", "elderly_rate", "log_income_pc_adj", "child_plus_elderly", "child_minus_elderly"])]:
        tab = "H2" if model == "ref_middle" else "H1"
        for i, t in enumerate(terms):
            lab = {"log_pop": d + "log_pop", "elderly_rate": d + "고령", "child_rate": d + "유소년", "youth_rate": d + "청년", "log_income_pc_adj": d + "log 소득", "child_plus_elderly": "child+elderly", "child_minus_elderly": "child−elderly"}[t]
            L.append(f"| {mn if i == 0 else ''} | {lab} | " + " | ".join(fmt(pick(table=tab, version=ver, fe=fe, dep=dep, model=model, term=t), t) for dep, _ in DEPS for fe, _ in FES) + " |")
    L.append("| nobs | | " + " | ".join(f"{int(pick(table='H1', version=ver, fe=fe, dep=dep, model='both', term='log_pop').nobs):,}" for dep, _ in DEPS for fe, _ in FES) + " |"); L.append("")
md = "\n".join(L); open(os.path.join(HERE, "table_fe_income.md"), "w", encoding="utf-8").write(md)
out, tbl = [], []
def flush():
    global tbl
    if not tbl: return
    rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in tbl if not re.match(r'^\|[-| ]+\|$', r.strip())]
    h = '<table border="1" style="border-collapse:collapse;font-size:8pt">'
    for i, r in enumerate(rows): tag = 'th' if i == 0 else 'td'; h += '<tr>' + ''.join(f'<{tag}>{html.escape(c)}</{tag}>' for c in r) + '</tr>'
    out.append(h + '</table>'); tbl = []
for line in L:
    if line.startswith('|'): tbl.append(line); continue
    flush()
    if line.startswith('### '): out.append(f'<h3>{html.escape(line[4:])}</h3>')
    elif line.startswith('## '): out.append(f'<h2>{html.escape(line[3:])}</h2>')
    elif line.strip(): out.append(f'<p>{html.escape(line)}</p>')
flush()
open(os.path.join(HERE, "table_fe_income.html"), "w", encoding="utf-8").write('<html><body>' + '\n'.join(out) + '</body></html>'); print(md)
