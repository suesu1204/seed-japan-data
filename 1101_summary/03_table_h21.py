"""H2-1 표 (연령층 하나씩): 행 = 연령층 × 고정효과, 열 = 수준 4 + 5년 차분 4. 출력 table_h21.md, table_h21.html"""
import os, re, html, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
C = pd.read_csv(os.path.join(HERE, "coefs_summary.csv")); C = C[C.table == "H2-1"]
def st(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def cell(ver, fe, dep, g):
    q = C[(C.version == ver) & (C.fe == fe) & (C.dep == dep) & (C.model == g) & (C.term == g + "_rate")]; assert len(q) == 1; x = q.iloc[0]
    return f"{x.coef:.4f} ({x.se_cluster:.4f}){st(x.p)}".replace("-", "−")
DEPS = ["land", "condo", "land_hedA", "condo_hedA"]; DN = ["중앙값 토지", "중앙값 아파트", "헤도닉 토지", "헤도닉 아파트"]
N = {"child": "유소년", "youth": "청년", "middle": "중장년", "elderly": "고령"}
L = ["## 연령층 하나씩 (log 가격 = log_pop + 해당 층 비중)", "",
     "칸 = 해당 층 비중 1%p ↑ (나머지 세 층이 현재 구성 비율대로 1%p ↓)일 때 log 가격 변화. 모형 4개를 따로 추정. 고령 행은 H1 '둘 다' 모형과 같음.", "",
     "| 연령층 | 고정효과 | 수준 회귀 | | | | 5년 장기차분 | | | |", "|" + "---|" * 10, "| | | " + " | ".join(DN) + " | " + " | ".join(DN) + " |"]
for g in N:
    for i, (fe, fn) in enumerate([("year", "지역+연도"), ("prefyear", "지역+현×연도")]):
        L.append(f"| {N[g] if i == 0 else ''} | {fn} | " + " | ".join(cell(ver, fe, d, g) for ver in ("level", "ld5") for d in DEPS) + " |")
md = "\n".join(L); open(os.path.join(HERE, "table_h21.md"), "w", encoding="utf-8").write(md)
rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in L if r.startswith('|') and not re.match(r'^\|[-| ]+\|$', r.strip())]
h = '<html><body><h2>' + html.escape(L[0][3:]) + '</h2><p>' + html.escape(L[2]) + '</p><table border="1" style="border-collapse:collapse;font-size:8pt">'
for i, r in enumerate(rows): tag = 'th' if i == 0 else 'td'; h += '<tr>' + ''.join(f'<{tag}>{html.escape(c)}</{tag}>' for c in r) + '</tr>'
open(os.path.join(HERE, "table_h21.html"), "w", encoding="utf-8").write(h + '</table></body></html>'); print(md)
