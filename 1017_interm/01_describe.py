"""1단계. 데이터 눈으로 보기 (계획서 1단계 그대로).

입력: panel.csv
출력: describe/  (표 csv + 그래프 png + describe.md 한 장)
  1. 변수별 평균, 최소, 최대, 결측 비율                       → summary.csv
  2. 시정촌 안에서 2010→2025 변한 양(인구, 고령 비중, 유소년 비중) → change_2010_2025.csv, change_summary.csv, change_hist.png
  3. 전국 연도별 추이 그래프(고령화율, 유소년 비중, 가격 3종)   → trend.csv, trend_shares.png, trend_prices.png
  4. 가격이 결측인 시정촌·연도가 어떤 곳인지                   → missing_profile.csv, missing_by_size.png
  5. 인구와 고령 비중의 within 상관/VIF                        → within_corr.csv, vif.csv
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "describe")
os.makedirs(OUT, exist_ok=True)

p = pd.read_csv(os.path.join(HERE, "panel.csv"), dtype={"muni_code": str, "pref_code": str})
assert p.shape[0] == 27856
PRICES = {"log_p_land": "토지만", "log_p_landbldg": "토지+건물", "log_p_condo": "아파트", "log_p_chika": "공시지가(주택지)"}
md = ["# 1단계. 데이터 눈으로 보기", "", "입력 `panel.csv` 27,856행(1,741 시정촌 × 2010~2025). 만든 스크립트 `01_describe.py`.", ""]


def table(df, floatfmt="{:.3f}"):
    return df.to_markdown(floatfmt=".3f")


# ---------- 1. 변수별 요약 ----------
cols = [c for c in p.columns if c not in ("muni_code", "year", "pref_code")]
s = p[cols].agg(["mean", "std", "min", "median", "max"]).T
s["결측비율"] = p[cols].isna().mean()
s.columns = ["평균", "표준편차", "최소", "중앙값", "최대", "결측비율"]
s.to_csv(os.path.join(OUT, "summary.csv"), encoding="utf-8-sig")
md += ["## 1. 변수별 평균·최소·최대·결측 비율", "", "avg3_* 열은 끝점 연도(2010/2015/2020/2025)에만 값이 있어 결측 비율이 높게 나옴.", "", table(s), ""]

# ---------- 2. 2010→2025 변화량 ----------
a = p[p.year == 2010].set_index("muni_code")
b = p[p.year == 2025].set_index("muni_code")
ch = pd.DataFrame({
    "pop_2010": a.pop_total, "pop_2025": b.pop_total,
    "인구변화율_%": (b.pop_total / a.pop_total - 1) * 100,
    "d_log_pop": b.log_pop - a.log_pop,
    "고령비중변화_%p": b.elderly_rate - a.elderly_rate,
    "유소년비중변화_%p": b.child_rate - a.child_rate,
    "청년비중변화_%p": b.youth_rate - a.youth_rate,
    "중장년비중변화_%p": b.middle_rate - a.middle_rate,
    "size_group": a.size_group, "kaso_dummy": a.kaso_dummy,
})
ch.to_csv(os.path.join(OUT, "change_2010_2025.csv"), encoding="utf-8-sig")
qs = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]
chcols = ["인구변화율_%", "고령비중변화_%p", "유소년비중변화_%p", "청년비중변화_%p", "중장년비중변화_%p"]
cs = ch[chcols].quantile(qs).T
cs.columns = ["최소", "p10", "p25", "중앙값", "p75", "p90", "최대"]
cs["평균"] = ch[chcols].mean()
cs_size = ch.groupby("size_group")[chcols].median().T
cs_size.columns = [f"규모{g} 중앙값" for g in cs_size.columns]
cs_kaso = ch.groupby("kaso_dummy")[chcols].median().T
cs_kaso.columns = ["비과소 중앙값", "과소 중앙값"]
cs = pd.concat([cs, cs_size, cs_kaso], axis=1)
cs.to_csv(os.path.join(OUT, "change_summary.csv"), encoding="utf-8-sig")
fig, ax = plt.subplots(1, 3, figsize=(14, 4))
for i, (c, t) in enumerate([("인구변화율_%", "인구 변화율 % (2010→2025)"), ("고령비중변화_%p", "고령 비중 변화 %p"), ("유소년비중변화_%p", "유소년 비중 변화 %p")]):
    ax[i].hist(ch[c].clip(ch[c].quantile(0.005), ch[c].quantile(0.995)), bins=50, color="#4C72B0")
    ax[i].axvline(ch[c].median(), color="k", ls="--", lw=1)
    ax[i].set_title(f"{t}\n중앙값 {ch[c].median():.1f}")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "change_hist.png"), dpi=130); plt.close(fig)
md += ["## 2. 시정촌 안에서 2010→2025 변한 양", "", "행 = 시정촌 1,741개. 규모 그룹 1 = 1만 미만, 2 = 1~5만, 3 = 5~20만, 4 = 20만 이상.", "",
       table(cs), "", "![](change_hist.png)", ""]

# ---------- 3. 전국 연도별 추이 ----------
tr = p.groupby("year").agg(고령화율_평균=("aging_rate", "mean"), 유소년비중_평균=("child_rate", "mean"),
                          청년비중_평균=("youth_rate", "mean"), 중장년비중_평균=("middle_rate", "mean"),
                          총인구_합계=("pop_total", "sum"))
for c, nm in PRICES.items():
    tr[f"{nm}_log가격_평균"] = p.groupby("year")[c].mean()
    tr[f"{nm}_값있는시정촌수"] = p.groupby("year")[c].count()
tr.to_csv(os.path.join(OUT, "trend.csv"), encoding="utf-8-sig")
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].plot(tr.index, tr.고령화율_평균, marker="o", label="고령화율(65+)")
ax[0].plot(tr.index, tr.유소년비중_평균, marker="o", label="유소년(0–14)")
ax[0].plot(tr.index, tr.청년비중_평균, marker="o", label="청년(15–34)")
ax[0].plot(tr.index, tr.중장년비중_평균, marker="o", label="중장년(35–64)")
ax[0].set_title("연령 비중 % (시정촌 단순평균)"); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].plot(tr.index, tr.총인구_합계 / 1e6, marker="o", color="k")
ax[1].set_title("총인구 합계 (백만 명)"); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "trend_shares.png"), dpi=130); plt.close(fig)
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
for c, nm in PRICES.items():
    y = tr[f"{nm}_log가격_평균"]
    ax[0].plot(tr.index, (y - y.iloc[0]) * 100, marker="o", label=nm)
    ax[1].plot(tr.index, tr[f"{nm}_값있는시정촌수"], marker="o", label=nm)
ax[0].set_title("log 가격 평균, 2010 대비 변화 (%)"); ax[0].axhline(0, color="gray", lw=.8); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].set_title("가격 값이 있는 시정촌 수"); ax[1].legend(); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "trend_prices.png"), dpi=130); plt.close(fig)
md += ["## 3. 전국 연도별 추이", "", "비중은 시정촌 단순평균(인구 가중 아님). 가격은 값 있는 시정촌의 log 가격 평균.", "",
       table(tr), "", "![](trend_shares.png)", "", "![](trend_prices.png)", ""]

# ---------- 4. 가격 결측 시정촌·연도 ----------
rows = []
for c, nm in PRICES.items():
    miss = p[c].isna()
    for lab, m in [("값 있음", ~miss), ("결측", miss)]:
        g = p[m]
        rows.append({"가격": nm, "구분": lab, "행 수": len(g), "비율": len(g) / len(p),
                     "고령화율 평균": g.aging_rate.mean(), "유소년비중 평균": g.child_rate.mean(),
                     "인구 중앙값": g.pop_total.median(), "과소 비율": g.kaso_dummy.mean(),
                     "규모1 비율": (g.size_group == 1).mean(), "규모2 비율": (g.size_group == 2).mean(),
                     "규모3 비율": (g.size_group == 3).mean(), "규모4 비율": (g.size_group == 4).mean()})
mp = pd.DataFrame(rows).set_index(["가격", "구분"])
never = {nm: int((p.groupby("muni_code")[c].count() == 0).sum()) for c, nm in PRICES.items()}
mp.to_csv(os.path.join(OUT, "missing_profile.csv"), encoding="utf-8-sig")
by_size = pd.DataFrame({nm: p.groupby("size_group")[c].apply(lambda s: s.isna().mean()) for c, nm in PRICES.items()})
fig, ax = plt.subplots(figsize=(7, 4))
by_size.plot.bar(ax=ax, rot=0)
ax.set_title("가격 결측 비율 (규모 그룹별)"); ax.set_xlabel("규모 그룹 (1=1만 미만 … 4=20만 이상)"); ax.set_ylim(0, 1); ax.grid(axis="y", alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "missing_by_size.png"), dpi=130); plt.close(fig)
md += ["## 4. 가격이 결측인 시정촌·연도가 어떤 곳인지", "",
       "결측 = 거래 5건 미만(공시지가는 지점 0). 16년 내내 한 번도 값이 없는 시정촌 수: " + ", ".join(f"{k} {v}곳" for k, v in never.items()) + ".", "",
       table(mp), "", "![](missing_by_size.png)", ""]

# ---------- 5. within 상관 / VIF ----------
X = ["log_pop", "child_rate", "youth_rate", "middle_rate", "elderly_rate"]
w = p[X] - p.groupby("muni_code")[X].transform("mean")   # 시정촌 평균을 뺀 값 (within)
wc = w.corr()
wc.to_csv(os.path.join(OUT, "within_corr.csv"), encoding="utf-8-sig")


def vif(df):
    out = {}
    for c in df.columns:
        y = df[c].to_numpy(); Z = np.column_stack([np.ones(len(df)), df.drop(columns=c).to_numpy()])
        r2 = 1 - ((y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        out[c] = 1 / (1 - r2)
    return pd.Series(out)


v = pd.DataFrame({"표 A (고령 비중 + log 인구)": vif(w[["elderly_rate", "log_pop"]]),
                  "표 H1-1 (유소년·청년·고령 + log 인구)": vif(w[["child_rate", "youth_rate", "elderly_rate", "log_pop"]])})
v.to_csv(os.path.join(OUT, "vif.csv"), encoding="utf-8-sig")
md += ["## 5. 인구와 고령 비중의 within 상관 / VIF", "", "within = 각 시정촌의 16년 평균을 뺀 값끼리의 상관. 고정효과 모형이 실제로 쓰는 변동.", "",
       table(wc), "", "VIF (within 변환 후). 빈칸은 그 모형에 안 들어가는 변수.", "", table(v), ""]

with open(os.path.join(OUT, "describe.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print("저장:", sorted(os.listdir(OUT)))
print(cs[["중앙값", "평균"]].round(2).to_string())
print("한 번도 가격 없는 시정촌:", never)
print(wc.round(2).to_string()); print(v.round(2).to_string())
