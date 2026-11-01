"""1031_bonus 표. 확인마다 (수준 / 차분) 표 하나. 열 = 기존(0_base) 4 + 이번 확인 4, 2행 헤더. 출력 chat_tables_bonus.md"""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
C = pd.read_csv(os.path.join(HERE, "coefs_bonus.csv")).fillna({"sub": ""}); C["sub"] = C["sub"].astype(str)
C.loc[C.check == "2_size", "sub"] = C.loc[C.check == "2_size", "sub"].map({"1": "1만 미만", "2": "1~5만", "3": "5~20만", "4": "20만 이상"})
def st(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def fmt(r, term):
    d = 3 if term == "log_pop" else 4
    return f"{r.coef:.{d}f} ({r.se_cluster:.{d}f}){st(r.p)}".replace("-", "−")
def pick(**k):
    q = C
    for a, b in k.items(): q = q[q[a] == b]
    assert len(q) <= 1, (k, len(q)); return None if len(q) == 0 else q.iloc[0]
DEPS = ["land", "condo", "land_hedA", "condo_hedA"]
SUBH = "중앙값 토지 | 중앙값 아파트 | 헤도닉A 토지 | 헤도닉A 아파트"
ROWS = [("H1", "pop_only", "log_pop", "인구만 · log_pop"), ("H1", "aging_only", "elderly_rate", "고령화만 · 고령"), ("H1", "aging_only", "share_65_74", "고령화만 · 65~74"), ("H1", "aging_only", "share_75p", "고령화만 · 75+"),
        ("H1", "both", "log_pop", "둘 다 · log_pop"), ("H1", "both", "elderly_rate", "둘 다 · 고령"), ("H1", "both", "share_65_74", "둘 다 · 65~74"), ("H1", "both", "share_75p", "둘 다 · 75+"),
        ("H2", "ref_middle", "log_pop", "H2 · log_pop"), ("H2", "ref_middle", "child_rate", "H2 · 유소년"), ("H2", "ref_middle", "youth_rate", "H2 · 청년"), ("H2", "ref_middle", "elderly_rate", "H2 · 고령"),
        ("H2", "ref_middle", "share_65_74", "H2 · 65~74"), ("H2", "ref_middle", "share_75p", "H2 · 75+"), ("H2", "ref_middle", "child_plus_elderly", "H2 · child+elderly"), ("H2", "ref_middle", "child_minus_elderly", "H2 · child−elderly")]
CHECKS = [("1_condo_sample", "1. 토지를 아파트 있는 시정촌만으로"), ("2_size", "2. 규모별 (2010년 인구)"), ("3_min_n", "3a. 거래 건수 하한"), ("3_weighted", "3b. 거래 건수 가중"),
          ("4_age_split", "4. 고령을 65~74 / 75+ 로 분리"), ("5_volume", "5. 종속변수 = log 거래 건수"), ("6_ld10", "6. 10년 장기차분"), ("7_fd1", "7. 1년 차분")]
VN = {"level": "수준 회귀", "ld5": "5년 장기차분", "ld10": "10년 장기차분", "fd1": "1년 차분"}
L = ["# 추가 확인 7종 (1031_bonus)", "",
     "소득 없음, 2010~2025 전체. 시정촌 + 현×연도FE(차분은 현×구간FE), 시정촌 군집. 칸 = 계수 (SE) 별표. 왼쪽 4열 = 기존 결과(전체 표본, 같은 사양으로 재추정; 1030_interm2·3과 동일), 오른쪽 4열 = 이번 확인. 빈칸 = 해당 없음 또는 표본 0.",
     "H2 = log 가격 = log_pop + 유소년 + 청년 + 고령 (중장년 기준). child+elderly, child−elderly = 유소년·고령 계수의 합·차(4번에서는 고령 = 65~74 + 75+).", ""]
for ck, title in CHECKS:
    L += [f"# {title}", ""]
    sub_ck = C[C.check == ck]
    for sub in sub_ck["sub"].drop_duplicates():
        for ver in [v for v in ["level", "ld5", "ld10", "fd1"] if v in sub_ck[sub_ck["sub"] == sub].version.unique()]:
            bver = "level" if ver == "level" else "ld5"
            head = f"기존 ({VN[bver]}, 전체)" if ck != "5_volume" else f"기존 log 가격 ({VN[bver]})"
            this = f"이번: {sub} ({VN[ver]})" if sub else f"이번 ({VN[ver]})"
            L += [f"**{VN[ver]}" + (f", {sub}" if sub and ck in ("2_size", "3_min_n") else "") + "**", "",
                  f"| 항 | {head} | | | | {this} | | | |", "|---" * 9 + "|", f"| | {SUBH} | {SUBH} |"]
            any_row = False
            for tab, model, term, lab in ROWS:
                cells = [pick(check="0_base", version=bver, dep=d, table=tab, model=model, term=term) for d in DEPS] + [pick(check=ck, sub=sub, version=ver, dep=d, table=tab, model=model, term=term) for d in DEPS]
                if all(c is None for c in cells[4:]): continue
                L.append(f"| {lab} | " + " | ".join("" if c is None else fmt(c, term) for c in cells) + " |"); any_row = True
            nb = [pick(check="0_base", version=bver, dep=d, table="H2", model="ref_middle", term="log_pop") for d in DEPS] + [pick(check=ck, sub=sub, version=ver, dep=d, table="H2", model="ref_middle", term="log_pop") for d in DEPS]
            L.append("| nobs | " + " | ".join("" if c is None else f"{int(c.nobs):,}" for c in nb) + " |"); L.append("")
open(os.path.join(HERE, "chat_tables_bonus.md"), "w", encoding="utf-8").write("\n".join(L)); print(len(L), "lines")
