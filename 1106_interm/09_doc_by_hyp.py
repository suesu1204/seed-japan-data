"""coefs_final.csv → results_by_hyp.md / .html. 가설(H1/H2/H3) × 방법(수준/장기차분/이동차분) = 표 9개, 표 안에서 표본 A/B/C 블록. 표마다 한 페이지."""
import os, html, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); c = pd.read_csv(os.path.join(HERE, "coefs_final.csv"))
def cell(x):
    if x is None: return "—"
    s = "***" if x.p < .01 else "**" if x.p < .05 else "*" if x.p < .1 else ""
    d = 3 if x.term in ("log_pop", "log_income_pc_adj") else 4
    return f"{x.coef:.{d}f} ({x.se:.{d}f}){s}".replace("-", "−")
def get(s, v, d, tab, model, term):
    x = c[(c["sample"] == s) & (c.version == v) & (c.dep == d) & (c.table == tab) & (c.model == model) & (c.term == term)]; return x.iloc[0] if len(x) else None
DEPN = {"condo": "아파트", "house": "단독주택", "resi": "주거용 건물(아파트+단독주택)"}; DEPS = ["condo", "house", "resi"]
SAMP = [("A", "A. 2010~2025, 소득 미통제"), ("B", "B. 2010~2024, 소득 미통제"), ("C", "C. 2010~2024, 소득 통제")]
VERS = [("level", "수준 회귀", "시정촌 고정효과 + 연도 고정효과"),
        ("ld5", "5년 장기차분 (비중첩)", "표본 A: 2010→15, 15→20, 20→25 세 구간. 표본 B·C: 2010→15, 15→20 두 구간. 구간 고정효과"),
        ("roll", "5년 이동차분", "t−5→t 변화. 표본 A: t = 2015~2025 (11구간). 표본 B·C: t = 2015~2024 (10구간). 종료연도 고정효과")]
HYP = [("H1", "가설 1: 인구 규모와 고령화율의 개별 효과 (식 (1), 인구만·고령화율만 각각 별도 회귀)",
        [("H1", "pop_only", "log_pop", "인구만: log 인구"), ("H1", "pop_only", "log_income_pc_adj", "인구만: log 소득"), ("H1", "aging_only", "elderly_rate", "고령화율만: 고령화율"), ("H1", "aging_only", "log_income_pc_adj", "고령화율만: log 소득")]),
       ("H2", "가설 2: 인구 규모를 통제한 고령화율 (식 (2))",
        [("H1", "both", "log_pop", "log 인구"), ("H1", "both", "elderly_rate", "고령화율"), ("H1", "both", "log_income_pc_adj", "log 소득")]),
       ("H3", "가설 3: 연령 구성 효과 (식 (3), 중장년 기준)",
        [("H3", "ref_middle", "log_pop", "log 인구"), ("H3", "ref_middle", "child_rate", "유소년 (δc)"), ("H3", "ref_middle", "youth_rate", "청년 (δy)"),
         ("H3", "ref_middle", "elderly_rate", "고령 (δe)"), ("H3", "ref_middle", "log_income_pc_adj", "log 소득"), ("H3", "ref_child", "elderly_rate", "고령, 유소년 기준 (δe − δc)")])]
intro = ["일본 주택 가격과 인구 구조: 가설별 결과 (2026-11-06)",
 "자료: 国土交通省 不動産情報ライブラリ 거래 건별 실거래가, 2010~2025. 아파트 = 中古マンション等, 전용면적당 가격. 단독주택 = 宅地(土地と建物) 중 건물 용도가 住宅인 거래(공동주택·점포 겸용 제외, 1,325,501건), 거래총액 ÷ 건물 연면적. 주거용 건물 = 아파트와 단독주택 거래를 한 풀로 묶은 중앙값. 시정촌·연도별 ㎡당 가격 중앙값의 log, 거래 5건 미만 결측. 토지(宅地(土地))는 제외.",
 "분석 단위: 1,741 시정촌(도쿄 23구 포함, 정령시는 시 단위). 설명변수: log 총인구, 연령대 비중(유소년 0~14 / 청년 15~34 / 중장년 35~64 / 고령 65+, %). 소득 = log 1인당 과세대상소득(課税対象所得 ÷ 납세의무자 수, 2024 소득연도 분모 보간), 2010~2024.",
 "식 (1) ln P = β X + FE, X = ln Pop 또는 Elderly (각각 별도 추정).  식 (2) ln P = β1 ln Pop + β2 Elderly + FE.  식 (3) ln P = β1 ln Pop + δc Child + δy Youth + δe Elderly + FE (중장년 기준).  표본 C는 각 식에 γ ln Income 추가. 차분 모형은 각 식의 5년 차분 형태.",
 "표 = 가설 3개 × 방법 3개(수준 / 5년 장기차분 / 5년 이동차분). 각 표 안에 표본 A·B·C 블록. 표준오차는 시정촌 군집. 칸 = 계수 (표준오차), *** 1%, ** 5%, * 10%.",
 "가설 3의 '고령, 유소년 기준' 행은 식 (3)에서 기준 범주만 유소년으로 바꾼 회귀의 고령 계수로, δe − δc와 같다(유소년 비중 1%p가 고령 비중 1%p로 대체될 때의 log 가격 변화).",
 "주의: 주거용 건물 칸의 66%는 아파트 거래가 0건이라 결과가 단독주택을 따라간다. 아파트와 단독주택을 따로 읽는 것이 정확하다."]
md = [f"# {intro[0]}\n"] + [t + "\n" for t in intro[1:]]
H = [f"<h1>{html.escape(intro[0])}</h1>"] + [f"<p>{html.escape(t)}</p>" for t in intro[1:]]
k = 0
for hkey, hname, rows in HYP:
    md.append(f"# {hname}\n"); H.append(f"<h1 style='page-break-before:always'>{html.escape(hname)}</h1>")
    for i, (v, vn, note) in enumerate(VERS):
        k += 1; title = f"표 {k}. {hkey} · {vn}"
        md.append(f"## {title}\n"); md.append(note + "\n")
        H.append(("<h2>" if i == 0 else "<h2 style='page-break-before:always'>") + f"{html.escape(title)}</h2><p>{html.escape(note)}</p>")
        hdr = ["표본", "변수"] + [DEPN[d] for d in DEPS]
        md.append("| " + " | ".join(hdr) + " |"); md.append("|---" * len(hdr) + "|")
        H.append("<table border='1' cellpadding='4' style='border-collapse:collapse'><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in hdr) + "</tr>")
        for s, sn in SAMP:
            first = True
            for tab, model, term, label in rows:
                if term == "log_income_pc_adj" and s != "C": continue
                vals = [cell(get(s, v, d, tab, model, term)) for d in DEPS]
                md.append(f"| {sn if first else ''} | {label} | " + " | ".join(vals) + " |")
                H.append("<tr>" + "".join(f"<td>{html.escape(x)}</td>" for x in [sn if first else "", label] + vals) + "</tr>"); first = False
            n = [f"{int(get(s, v, d, rows[0][0], rows[0][1], rows[0][2]).nobs):,}" for d in DEPS]
            md.append("| | 관측치 | " + " | ".join(n) + " |"); H.append("<tr>" + "".join(f"<td>{x}</td>" for x in ["", "관측치"] + n) + "</tr>")
        md.append(""); H.append("</table>")
g = get
def ct(s_, v_, d_, tab="H1", model="both", term="elderly_rate"):
    x = g(s_, v_, d_, tab, model, term); return f"{x.coef:.4f}{'***' if x.p < .01 else '**' if x.p < .05 else '*' if x.p < .1 else ''}".replace("-", "−")
summ = [("가설 1", "세 종속변수 모두 인구만 넣은 회귀의 log 인구는 양(+), 고령화율만 넣은 회귀의 고령화율은 음(−)으로 1% 수준 유의. 세 표본·세 방법에서 동일. 가설 1 지지."),
 ("가설 2", f"아파트는 표본 A·B·C, 수준·장기차분·이동차분 아홉 칸 모두 유의한 음(−). 표본 C 기준 수준 {ct('C','level','condo')}, 장기차분 {ct('C','ld5','condo')}, 이동차분 {ct('C','roll','condo')}. 단독주택은 소득 미통제 표본 A에서 음(−)이지만 약함(수준 {ct('A','level','house')}, 장기차분 {ct('A','ld5','house')}, 이동차분 {ct('A','roll','house')}), 소득 통제 후에는 세 방법 모두 유의하지 않음({ct('C','level','house')}, {ct('C','ld5','house')}, {ct('C','roll','house')}). 주거용 건물은 단독주택과 같은 패턴. 가설 2는 아파트에서 지지, 단독주택에서 기각."),
 ("가설 3", f"아파트는 중장년 기준에서 유소년 양(+), 고령 음(−) 또는 0. 유소년 기준 고령 계수(δe − δc)는 아파트의 수준·이동차분에서 세 표본 모두 음(−)이고 10% 이내 유의(표본 C 수준 {ct('C','level','condo','H3','ref_child')}, 이동차분 {ct('C','roll','condo','H3','ref_child')}). 비중첩 장기차분에서는 표본 A만 10% 유의({ct('A','ld5','condo','H3','ref_child')})이고 B·C(두 구간, n={int(g('C','ld5','condo','H3','ref_child','elderly_rate').nobs)})에서는 유의하지 않음. 단독주택은 표본 A 수준({ct('A','level','house','H3','ref_child')}) 외에는 어느 칸에서도 유의하지 않음."),
 ("표본 간 비교", f"A→B(2025년 제외)는 계수가 거의 변하지 않음. B→C(소득 추가)에서 고령화율 계수가 줄어듦: 아파트 수준 {ct('B','level','condo')}→{ct('C','level','condo')}, 단독주택 {ct('B','level','house')}→{ct('C','level','house')}. 아파트는 소득 통제 후에도 유지되고 단독주택은 0이 됨.")]
assert all(g(s_, v_, "condo", "H1", "both", "elderly_rate").p < .05 and g(s_, v_, "condo", "H1", "both", "elderly_rate").coef < 0 for s_ in "ABC" for v_ in ["level", "ld5", "roll"])
assert all(g("C", v_, "house", "H1", "both", "elderly_rate").p > .1 for v_ in ["level", "ld5", "roll"])
assert g("A", "level", "house", "H1", "both", "elderly_rate").p < .1 and all(g("A", v_, "house", "H1", "both", "elderly_rate").p < .05 for v_ in ["ld5", "roll"])
assert all(g(s_, v_, d_, "H1", m_, t_).p < .01 and (g(s_, v_, d_, "H1", m_, t_).coef > 0) == (t_ == "log_pop") for s_ in "ABC" for v_ in ["level", "ld5", "roll"] for d_ in DEPS for m_, t_ in [("pop_only", "log_pop"), ("aging_only", "elderly_rate")]), "H1 주장"
assert all(g(s_, v_, "condo", "H3", "ref_child", "elderly_rate").p < .1 and g(s_, v_, "condo", "H3", "ref_child", "elderly_rate").coef < 0 for s_ in "ABC" for v_ in ["level", "roll"])
assert g("A", "ld5", "condo", "H3", "ref_child", "elderly_rate").p < .1 and all(g(s_, "ld5", "condo", "H3", "ref_child", "elderly_rate").p > .1 for s_ in "BC")
hp = [(s_, v_) for s_ in "ABC" for v_ in ["level", "ld5", "roll"] if g(s_, v_, "house", "H3", "ref_child", "elderly_rate").p < .1]; assert hp == [("A", "level")], hp
md.append("# 요약\n"); md += [f"- **{a}**: {b}" for a, b in summ]
H.append("<h1 style='page-break-before:always'>요약</h1><ul>" + "".join(f"<li><b>{html.escape(a)}</b>: {html.escape(b)}</li>" for a, b in summ) + "</ul>")
open(os.path.join(HERE, "results_by_hyp.md"), "w", encoding="utf-8").write("\n".join(md))
open(os.path.join(HERE, "results_by_hyp.html"), "w", encoding="utf-8").write("<html><head><meta charset='utf-8'></head><body>" + "\n".join(H) + "</body></html>")
print("요약 검증 통과; results_by_hyp.md / .html")
