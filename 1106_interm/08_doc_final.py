"""coefs_final.csv → results_final.md / results_final.html. 표본(A/B/C) × 방법(수준/장기차분/이동차분) = 표 9개, 표마다 한 페이지."""
import os, html, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); c = pd.read_csv(os.path.join(HERE, "coefs_final.csv"))
def cell(x):
    if x is None: return "—"
    s = "***" if x.p < .01 else "**" if x.p < .05 else "*" if x.p < .1 else ""
    d = 3 if x.term in ("log_pop", "log_income_pc_adj") else 4
    return f"{x.coef:.{d}f} ({x.se:.{d}f}){s}".replace("-", "−")
def get(s, v, d, tab, model, term):
    x = c[(c["sample"] == s) & (c.version == v) & (c.dep == d) & (c.table == tab) & (c.model == model) & (c.term == term)]; return x.iloc[0] if len(x) else None
ROWS = [("H1", "pop_only", "log_pop", "H1 인구만", "log 인구"), ("H1", "aging_only", "elderly_rate", "H1 고령화만", "고령화율"),
        ("H1", "both", "log_pop", "H2 둘 다", "log 인구"), ("H1", "both", "elderly_rate", "H2 둘 다", "고령화율"),
        ("H3", "ref_middle", "log_pop", "H3 (중장년 기준)", "log 인구"), ("H3", "ref_middle", "child_rate", "H3 (중장년 기준)", "유소년"),
        ("H3", "ref_middle", "youth_rate", "H3 (중장년 기준)", "청년"), ("H3", "ref_middle", "elderly_rate", "H3 (중장년 기준)", "고령"),
        ("H3", "ref_middle", "log_income_pc_adj", "H3 (중장년 기준)", "log 소득"), ("H3", "ref_child", "elderly_rate", "H3 (유소년 기준)", "고령 (= 유소년→고령 교환효과)")]
DEPN = {"condo": "아파트", "house": "단독주택", "resi": "주거용 건물(아파트+단독주택)"}; DEPS = ["condo", "house", "resi"]
SAMP = [("A", "표본 A: 2010~2025, 소득 미통제"), ("B", "표본 B: 2010~2024, 소득 미통제"), ("C", "표본 C: 2010~2024, 소득 통제")]
VERS = [("level", "수준 회귀", "시정촌 고정효과 + 연도 고정효과"),
        ("ld5", "5년 장기차분 (비중첩)", {"A": "2010→15, 15→20, 20→25 세 구간, 구간 고정효과", "B": "2010→15, 15→20 두 구간, 구간 고정효과", "C": "2010→15, 15→20 두 구간, 구간 고정효과"}),
        ("roll", "5년 이동차분", {"A": "t−5→t, t = 2015~2025 (11구간), 종료연도 고정효과", "B": "t−5→t, t = 2015~2024 (10구간), 종료연도 고정효과", "C": "t−5→t, t = 2015~2024 (10구간), 종료연도 고정효과"})]
intro = ["일본 주택 가격과 인구 구조: 최종 사양 결과 (2026-11-06)",
 "자료: 国土交通省 不動産情報ライブラリ 거래 건별 실거래가, 2010~2025. 아파트 = 中古マンション等, 전용면적당 가격. 단독주택 = 宅地(土地と建物) 중 건물 용도가 住宅인 거래(공동주택·점포 겸용 제외, 1,322,915건), 거래총액 ÷ 건물 연면적. 주거용 건물 = 아파트와 단독주택 거래를 한 풀로 묶은 중앙값. 시정촌·연도별 ㎡당 가격 중앙값의 log, 거래 5건 미만 결측. 토지(宅地(土地))는 제외.",
 "분석 단위: 1,741 시정촌(도쿄 23구 포함, 정령시는 시 단위). 설명변수: log 총인구, 연령대 비중(유소년 0~14 / 청년 15~34 / 중장년 35~64 / 고령 65+, %). 소득 = log 1인당 과세대상소득(課税対象所得 ÷ 납세의무자 수, 2024 소득연도 분모 보간), 2010~2024.",
 "표본 3종 × 방법 3종 = 표 9개. 표준오차는 시정촌 군집. 칸 = 계수 (표준오차), *** 1%, ** 5%, * 10%.",
 "H3 '유소년 기준' 행은 같은 식 (4)에서 기준 범주만 유소년으로 바꾼 것으로, 고령 계수 = δe − δc (유소년 비중 1%p가 고령 비중 1%p로 대체될 때의 log 가격 변화).",
 "주의: 주거용 건물 칸의 66%는 아파트 거래가 0건이라 결과가 단독주택을 따라간다. 아파트와 단독주택을 따로 읽는 것이 정확하다."]
md = [f"# {intro[0]}\n"] + [t + "\n" for t in intro[1:]]
H = [f"<h1>{html.escape(intro[0])}</h1>"] + [f"<p>{html.escape(t)}</p>" for t in intro[1:]]
k = 0
for s, sn in SAMP:
    for v, vn, note in VERS:
        k += 1; note = note if isinstance(note, str) else note[s]; title = f"표 {k}. {sn} · {vn}"
        md.append(f"## {title}\n"); md.append(note + "\n")
        H.append(f"<h2 style='page-break-before:always'>{html.escape(title)}</h2><p>{html.escape(note)}</p>")
        hdr = ["모형", "변수"] + [DEPN[d] for d in DEPS]
        md.append("| " + " | ".join(hdr) + " |"); md.append("|---" * len(hdr) + "|")
        H.append("<table border='1' cellpadding='4' style='border-collapse:collapse'><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in hdr) + "</tr>")
        for tab, model, term, mn, vnm in ROWS:
            if term == "log_income_pc_adj" and s != "C": continue
            vals = [cell(get(s, v, d, tab, model, term)) for d in DEPS]
            md.append(f"| {mn} | {vnm} | " + " | ".join(vals) + " |"); H.append("<tr>" + "".join(f"<td>{html.escape(x)}</td>" for x in [mn, vnm] + vals) + "</tr>")
        n = [f"{int(get(s, v, d, 'H1', 'both', 'elderly_rate').nobs):,}" for d in DEPS]
        md.append("| 관측치 | | " + " | ".join(n) + " |\n"); H.append("<tr>" + "".join(f"<td>{x}</td>" for x in ["관측치", ""] + n) + "</tr></table>")
g = lambda s_, v_, d_, tab, model, term: get(s_, v_, d_, tab, model, term)
def ct(s_, v_, d_, tab="H1", model="both", term="elderly_rate"): x = g(s_, v_, d_, tab, model, term); return f"{x.coef:.4f}{'***' if x.p < .01 else '**' if x.p < .05 else '*' if x.p < .1 else ''}".replace("-", "−")
summ = ["요약",
 "H1(개별 효과): 세 종속변수 모두 log 인구는 양(+), 고령화율은 음(−)으로 1% 수준 유의. 모든 표본·방법에서 동일.",
 f"H2(인구 통제 후 고령화율): 아파트는 표본 A·B·C, 수준·장기차분·이동차분 아홉 칸 모두 유의한 음(−). 표본 C 기준 수준 {ct('C','level','condo')}, 장기차분 {ct('C','ld5','condo')}, 이동차분 {ct('C','roll','condo')}. 단독주택은 소득 미통제에서 장기차분·이동차분만 음(−)·유의(표본 A {ct('A','ld5','house')}, {ct('A','roll','house')})이고 수준에서는 0({ct('A','level','house')}), 소득 통제 후에는 세 방법 모두 유의하지 않음({ct('C','level','house')}, {ct('C','ld5','house')}, {ct('C','roll','house')}). 주거용 건물은 단독주택과 같은 패턴.",
 f"H3: 아파트는 중장년 기준에서 유소년 양(+), 고령 음(−) 또는 0. 유소년 기준으로 바꾼 교환효과(δe − δc)는 아파트의 수준·이동차분에서 세 표본 모두 음(−)이고 10% 이내 유의(표본 C 수준 {ct('C','level','condo','H3','ref_child')}, 이동차분 {ct('C','roll','condo','H3','ref_child')}). 비중첩 장기차분에서는 표본 A만 10% 유의({ct('A','ld5','condo','H3','ref_child')})이고 B·C(두 구간, n={int(g('C','ld5','condo','H3','ref_child','elderly_rate').nobs)})에서는 유의하지 않음. 단독주택은 표본 A 수준({ct('A','level','house','H3','ref_child')}) 외에는 어느 칸에서도 유의하지 않음.",
 f"표본 A→B(2025년 제외)는 계수가 거의 변하지 않음. B→C(소득 추가)에서 고령화율 계수가 줄어듦: 아파트 수준 {ct('B','level','condo')}→{ct('C','level','condo')}, 단독주택 {ct('B','level','house')}→{ct('C','level','house')}. 아파트는 소득 통제 후에도 유지되고 단독주택은 0이 됨."]
assert all(g(s_, v_, "condo", "H1", "both", "elderly_rate").p < .05 and g(s_, v_, "condo", "H1", "both", "elderly_rate").coef < 0 for s_ in "ABC" for v_ in ["level", "ld5", "roll"]), "아파트 H2 아홉 칸"
assert all(g("C", v_, "house", "H1", "both", "elderly_rate").p > .1 for v_ in ["level", "ld5", "roll"]), "단독 C 비유의"
assert g("A", "level", "house", "H1", "both", "elderly_rate").p > .1 and all(g("A", v_, "house", "H1", "both", "elderly_rate").p < .05 for v_ in ["ld5", "roll"]), "단독 A"
assert all(g(s_, v_, "condo", "H3", "ref_child", "elderly_rate").p < .1 and g(s_, v_, "condo", "H3", "ref_child", "elderly_rate").coef < 0 for s_ in "ABC" for v_ in ["level", "roll"]), "아파트 교환효과 수준·이동"
assert g("A", "ld5", "condo", "H3", "ref_child", "elderly_rate").p < .1 and all(g(s_, "ld5", "condo", "H3", "ref_child", "elderly_rate").p > .1 for s_ in "BC"), "아파트 교환효과 장기차분"
hp = [(s_, v_) for s_ in "ABC" for v_ in ["level", "ld5", "roll"] if g(s_, v_, "house", "H3", "ref_child", "elderly_rate").p < .1]; assert hp == [("A", "level")], hp
md.append(f"## {summ[0]}\n"); md += [f"- {t}" for t in summ[1:]]
H.append(f"<h2 style='page-break-before:always'>{summ[0]}</h2><ul>" + "".join(f"<li>{html.escape(t)}</li>" for t in summ[1:]) + "</ul>")
open(os.path.join(HERE, "results_final.md"), "w", encoding="utf-8").write("\n".join(md))
open(os.path.join(HERE, "results_final.html"), "w", encoding="utf-8").write("<html><head><meta charset='utf-8'></head><body>" + "\n".join(H) + "</body></html>")
print("요약 검증 통과; results_final.md / .html")
