"""정리본: 0 헤도닉 설명 / 1 고정효과 비교표 / 2 교환효과 표 4개. 입력 coefs_summary.csv → summary.md, summary.html"""
import os, re, html, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
C = pd.read_csv(os.path.join(HERE, "coefs_summary.csv"))
def st(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def pick(**k):
    q = C
    for a, b in k.items(): q = q[q[a] == b]
    assert len(q) == 1, (k, len(q)); return q.iloc[0]
def fmt(x, term): d = 3 if term == "log_pop" else 4; return f"{x.coef:.{d}f} ({x.se_cluster:.{d}f}){st(x.p)}".replace("-", "−")
DEPS = [("land", "중앙값 토지"), ("condo", "중앙값 아파트"), ("land_hedA", "헤도닉 토지"), ("condo_hedA", "헤도닉 아파트")]
FES = [("year", "지역+연도"), ("prefyear", "지역+현×연도")]
N = {"child": "유소년", "youth": "청년", "middle": "중장년", "elderly": "고령"}
L = ["# 일본 분석 정리 (2026-11-01)", "",
     "표본: 1,741 시정촌(도쿄 23구 포함, 정령시는 시 단위) × 2010~2025. 가격 = ㎡당 가격 log(중앙값 또는 헤도닉 지수), 5건 미만 결측. 설명변수 = log 인구, 연령대 비중(유소년 0~14 / 청년 15~34 / 중장년 35~64 / 고령 65+, %). 5년 장기차분 = 2010→15, 15→20, 20→25 끝점 차. 표준오차는 시정촌 군집. 칸 = 계수 (SE) 별표(*** 1%, ** 5%, * 10%). 소득 통제는 포함하지 않음.", "",
     "# 0. 헤도닉 가격지수", "",
     "목적: 시정촌·연도별 중앙값은 그 해 어떤 필지·호가 거래됐느냐에 따라 흔들린다. 거래 속성을 통제한 뒤 남는 시정촌×연도 수준을 가격지수로 쓴다 (Saita, Shimizu, Watanabe 2016 식 (2) 방식).", "",
     "식: ln p_i = Σ β·X_i + θ_{시정촌×연도} + ε_i. 거래 건별 회귀를 전국 한 번에 돌려 속성 계수 β는 전국 공통, θ(시정촌×연도 고정효과 추정치)가 지수. 회귀에 들어간 거래가 5건 미만인 시정촌·연도는 결측. 입력은 reinfolib 거래 건별 원자료 2010~2025 (토지만 宅地(土地), 아파트 中古マンション等).", "",
     "토지 속성 (사양 A, 한국 자료와 공통인 항목): ln 면적 (면적 9999 코드는 ≥2,000㎡ 표시이므로 거래가÷㎡단가로 역산하고 big_lot 더미 추가), 용도지역 더미(第１種住居地域 기준, 빈칸은 '불명' 범주), 전면도로 폭 구간 더미(8m 미만 / 8~12 / 12~25 / 25m 이상 / 불명). 종속변수는 reinfolib가 제공하는 ㎡단가(UnitPrice)의 log. 1,000엔 미만 거래를 제외하는 규칙은 두지 않음(하한 없음 버전).", "",
     "아파트 속성: ln 전용면적, 건물 연령(거래연도 − 건축연도, 戦前은 1945년으로, 음수는 0, 건축연도 빈칸은 표본 평균으로 대체 + age_na 더미). 면적 9999 행은 제외.", "",
     "확인한 것: (1) 토지 사양 A에 1,000엔 하한을 두면 고령 계수가 절반으로 약해지는데, 하한을 빼면 중앙값 결과와 같아져 하한이 원인이었음. 본 정리는 하한 없음. (2) Saita 속성(면적·건폐율·용적률)으로 만든 사양 B는 A보다 결과가 약해 본 정리에서 제외. (3) 아파트는 사양 A·B 차이 없음.", "",
     "# 1. 고정효과 변경: 지역+연도 → 지역+현×연도", "",
     "기존 모형은 시정촌 고정효과 + 연도 고정효과(전국 공통 연도 충격). 수정 모형은 연도 고정효과를 도도부현×연도로 바꿔 현 단위의 연도별 충격(지역 경기, 재해, 현 정책)을 흡수. 장기차분에서는 구간 → 현×구간. 아래 표는 같은 표본에서 두 고정효과를 나란히 둔 것. 식: H1 = log 가격 ~ log_pop 및/또는 고령 비중. H2 = log 가격 ~ log_pop + 유소년 + 청년 + 고령 비중(중장년 기준). child+elderly = 유소년·고령 계수의 합(Wald), child−elderly = 차.", ""]
def head2(first):
    k = first.count("|") + 1
    return ["| " + first + " | " + " | ".join(f"{dn} | " for _, dn in DEPS) + "|", "|" + "---|" * (k + 8),
            "| " + " | ".join([""] * k) + " | " + " | ".join("지역+연도 | 지역+현×연도" for _ in DEPS) + " |"]
for ver, vn in [("level", "수준 회귀"), ("ld5", "5년 장기차분")]:
    d = "Δ" if ver == "ld5" else ""
    L += [f"## 1-{1 if ver == 'level' else 2}. {vn}", ""] + head2("모형 | 항")
    for model, mn, terms in [("pop_only", "H1 인구만", ["log_pop"]), ("aging_only", "H1 고령화만", ["elderly_rate"]), ("both", "H1 둘 다", ["log_pop", "elderly_rate"]),
                             ("ref_middle", "H2 (중장년 기준)", ["log_pop", "child_rate", "youth_rate", "elderly_rate", "child_plus_elderly", "child_minus_elderly"])]:
        tab = "H2" if model == "ref_middle" else "H1"
        for i, t in enumerate(terms):
            lab = {"log_pop": d + "log_pop", "elderly_rate": d + "고령", "child_rate": d + "유소년", "youth_rate": d + "청년", "child_plus_elderly": "child+elderly", "child_minus_elderly": "child−elderly"}[t]
            L.append(f"| {mn if i == 0 else ''} | {lab} | " + " | ".join(fmt(pick(table=tab, version=ver, fe=fe, dep=dep, model=model, term=t), t) for dep, _ in DEPS for fe, _ in FES) + " |")
    L.append("| nobs | | " + " | ".join(f"{int(pick(table='H1', version=ver, fe=fe, dep=dep, model='both', term='log_pop').nobs):,}" for dep, _ in DEPS for fe, _ in FES) + " |"); L.append("")
L += ["# 2. 연령층 교환 효과", "",
      "비중 4개는 합이 100이라 한 층이 늘면 다른 층이 줄어야 한다. 'A ↔ B' 칸은 A 비중 1%p ↓, B 비중 1%p ↑(나머지 그대로)일 때 log 가격 변화 = A를 기준 범주로 둔 회귀에서 B 비중의 계수. 모형이 비중에 선형이므로 반대 방향(A ↑, B ↓)은 부호만 반대이고 크기는 같다. 6쌍이 전부이며 표 4개에 각 쌍이 두 번 나타난다. H3(유소년 감소 vs 고령 증가)에 해당하는 칸은 '유소년 ↔ 고령'.", ""]
def head3(first):
    k = first.count("|") + 1
    return ["| " + first + " | 수준 회귀 | | | | 5년 장기차분 | | | |", "|" + "---|" * (k + 8),
            "| " + " | ".join([""] * k) + " | " + " | ".join(dn for _, dn in DEPS) + " | " + " | ".join(dn for _, dn in DEPS) + " |"]
for a in N:
    L += [f"## 2-{list(N).index(a) + 1}. {N[a]} ↔ 다른 층  ({N[a]} 1%p ↓, 상대 1%p ↑)", ""] + head3("상대 | 고정효과")
    for b in [g for g in N if g != a]:
        for i, (fe, fn) in enumerate(FES):
            cells = [fmt(pick(table="H2", version=ver, fe=fe, dep=dep, model="ref_" + a, term=b + "_rate"), b) for ver in ("level", "ld5") for dep, _ in DEPS]
            L.append(f"| {N[a] + ' ↔ ' + N[b] if i == 0 else ''} | {fn} | " + " | ".join(cells) + " |")
    L.append("")
L += ["## nobs (교환 효과 표)", "", "| 고정효과 | " + " | ".join(dn for _, dn in DEPS) + " | " + " | ".join(dn for _, dn in DEPS) + " |", "|" + "---|" * 9]
for fe, fn in FES: L.append(f"| {fn} | " + " | ".join(f"{int(pick(table='H2', version=ver, fe=fe, dep=dep, model='ref_middle', term='log_pop').nobs):,}" for ver in ("level", "ld5") for dep, _ in DEPS) + " |")
md = "\n".join(L); open(os.path.join(HERE, "summary.md"), "w", encoding="utf-8").write(md)
# HTML
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
open(os.path.join(HERE, "summary.html"), "w", encoding="utf-8").write('<html><body>' + '\n'.join(out) + '</body></html>')
print(len(L), "lines;", md.count("\n## "), "sections")
