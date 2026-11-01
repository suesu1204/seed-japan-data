"""비선형 확인 표. A·B·C는 고정효과 2종(지역+연도 / 지역+현×연도)을 행으로. D(추가 확인)는 현×연도만. 출력 chat_tables_nonlinear.md, .html"""
import os, re, html, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
C = pd.read_csv(os.path.join(HERE, "coefs_nonlinear.csv")); K = pd.read_csv(os.path.join(HERE, "coefs_checks.csv"))
def st(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def fmtx(x, d=4):
    if pd.isna(x.se_cluster): return f"p = {x.coef:.3f}"
    return f"{x.coef:.{d}f} ({x.se_cluster:.{d}f}){st(x.p)}".replace("-", "−")
def cell(design, fe, dep, term, d=4):
    q = C[(C.design == design) & (C.fe == fe) & (C.dep == dep) & (C.term == term)]; assert len(q) == 1, (design, fe, dep, term); return fmtx(q.iloc[0], d)
DEPS = ["land", "condo", "land_hedA", "condo_hedA"]; DN = "| 중앙값 토지 | 중앙값 아파트 | 헤도닉 토지 | 헤도닉 아파트 |"
FES = [("year", "지역+연도"), ("prefyear", "지역+현×연도")]
H = ["| 항 | 고정효과 " + DN, "|---|---|---|---|---|---|"]
def block(design, rows, dig):
    out = []
    for t, lab in rows:
        for i, (fe, fn) in enumerate(FES): out.append(f"| {lab if i == 0 else ''} | {fn} | " + " | ".join(cell(design, fe, d, t, dig.get(t, 4)) for d in DEPS) + " |")
    out.append("| nobs | | " + " | ".join(f"{int(C[(C.design == design) & (C.dep == d)].nobs.iloc[0]):,}" for d in DEPS) + " |")
    return out
L = ["# 고령 비중 비선형 확인 (1101_nonlinear)", "",
     "소득 없음, 2010~2025. 기본식 log 가격 = 고령 비중 + log_pop. 고정효과 2종: 지역+연도(차분은 구간) / 지역+현×연도(차분은 현×구간). 시정촌 군집. 헤도닉 토지 = 사양 A 하한 없음. 칸 = 계수 (SE) 별표. 한계효과·기울기 단위 = 고령 1%p당 log 가격 변화.", "",
     "## A. 제곱항 (수준 회귀) — log 가격 = β₁·고령 + β₂·고령² + γ·log_pop", ""] + H
L += block("A_quad", [("elderly_rate", "β₁ 고령"), ("eld2", "β₂ 고령²"), ("log_pop", "log_pop"), ("me_at_25", "한계효과 @ 고령 25%"), ("me_at_32", "한계효과 @ 32% (평균)"), ("me_at_40", "한계효과 @ 40%")], {"eld2": 5, "log_pop": 3})
L += ["", "## B. 구간별 기울기 (수준 회귀) — 꺾은선, 매듭 28%·35% (전체 표본 3분위)", ""] + H
L += block("B_spline", [("slope_lt28", "기울기: 고령 < 28%"), ("slope_28_35", "기울기: 28~35%"), ("slope_ge35", "기울기: ≥ 35%"), ("log_pop", "log_pop"), ("wald_equal_slopes_p", "기울기 동일성 Wald")], {"log_pop": 3})
L += ["", "## C. 출발 수준 × 변화 (5년 장기차분) — Δlog 가격 = β₁·Δ고령 + β₂·Δ고령 × 고령₂₀₁₀ + γ·Δlog_pop", ""] + H
L += block("C_start_x_change", [("elderly_rate", "β₁ Δ고령"), ("dxe", "β₂ Δ고령 × 고령₂₀₁₀"), ("log_pop", "Δlog_pop"), ("eff_at_start_20", "Δ고령 효과 @ 2010년 고령 20%"), ("eff_at_start_30", "@ 30%"), ("eff_at_start_40", "@ 40%")], {"dxe": 5, "log_pop": 3})
# D (현×연도만)
def kc(ck, d, t):
    x = K[(K.check == ck) & (K.dep == d) & (K.term == t)].iloc[0]
    return f"{int(x.coef):,}" if t == "n_ge35" else fmtx(x)
L += ["", "## D. B(구간별 기울기) 추가 확인 — 지역+현×연도만", "",
      "고령 ≥ 35%에서 아파트 거래가 있는 시정촌 27곳(121행)은 리조트가 아니라 小樽·下関·函館·呉·大牟田 같은 지방 중핵도시와 三浦·南知多·河内長野·取手 같은 대도시권 외곽(목록 checks_condo_ge35.csv). 이름 기준 리조트 플래그는 別府 1곳.", "",
      "| 확인 | 항 " + DN, "|---|---|---|---|---|---|"]
for ck, cn in [("0_base", "기본 B"), ("1_no_resort", "리조트 플래그 제외 (別府만)"), ("2_logpop_sq", "+ log_pop²"), ("3_sizegroup_year", "+ 규모그룹×연도 FE")]:
    for t, lab in [("slope_lt28", "기울기 < 28%"), ("slope_28_35", "28~35%"), ("slope_ge35", "≥ 35%"), ("n_ge35", "≥35% 행 수"), ("wald_equal_slopes_p", "동일성 Wald")]:
        L.append(f"| {cn if t == 'slope_lt28' else ''} | {lab} | " + " | ".join(kc(ck, d, t) for d in DEPS) + " |")
md = "\n".join(L) + "\n"; open(os.path.join(HERE, "chat_tables_nonlinear.md"), "w", encoding="utf-8").write(md)
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
    if line.startswith('## '): out.append(f'<h2>{html.escape(line[3:])}</h2>')
    elif line.startswith('# '): out.append(f'<h1>{html.escape(line[2:])}</h1>')
    elif line.strip(): out.append(f'<p>{html.escape(line)}</p>')
flush()
open(os.path.join(HERE, "chat_tables_nonlinear.html"), "w", encoding="utf-8").write('<html><body>' + '\n'.join(out) + '</body></html>'); print(len(L), "lines")
