"""일본 고령화율(65세 이상 비중, %) 수준 비교용 기술통계, 2010~2025. 전체 1,741 시정촌 + 아파트 표본(log_p_condo 있는 칸).
출력 aging_desc.csv, aging_desc.md, aging_trend.png"""
import os, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
p = pd.read_csv(os.path.join(HERE, "panel_v5.csv"), dtype={"muni_code": str}, usecols=["muni_code", "year", "pop_total", "elderly_rate", "log_p_condo"])
def stats(g): return pd.Series({"인구가중": np.average(g.elderly_rate, weights=g.pop_total), "단순평균": g.elderly_rate.mean(),
    "p25": g.elderly_rate.quantile(.25), "중앙값": g.elderly_rate.median(), "p75": g.elderly_rate.quantile(.75), "n": len(g)})
a = p.groupby("year").apply(stats, include_groups=False)
c = p[p.log_p_condo.notna()].groupby("year").apply(stats, include_groups=False)
out = a.join(c[["인구가중", "중앙값", "n"]].rename(columns=lambda s: "아파트표본_" + s))
out.round(2).to_csv(os.path.join(HERE, "aging_desc.csv"), encoding="utf-8-sig")
md = ["# 일본 고령화율 수준 (65세 이상 비중, %)\n", "전체 = 1,741 시정촌(도쿄 23구 포함). 인구가중 = Σ65세 이상 / Σ총인구. 분위수는 시정촌 분포. 아파트 표본 = 그해 아파트 가격이 있는 시정촌(5건 이상).\n",
      "| 연도 | 인구가중 | 단순평균 | p25 | 중앙값 | p75 | 아파트표본 인구가중 | 아파트표본 중앙값 | 아파트표본 n |", "|---|---|---|---|---|---|---|---|---|"]
for y, r in out.iterrows(): md.append(f"| {y} | {r['인구가중']:.1f} | {r['단순평균']:.1f} | {r['p25']:.1f} | {r['중앙값']:.1f} | {r['p75']:.1f} | {r['아파트표본_인구가중']:.1f} | {r['아파트표본_중앙값']:.1f} | {int(r['아파트표본_n'])} |")
d = out.loc[2025] - out.loc[2010]
md.append(f"\n2010→2025 변화(%p): 인구가중 +{d['인구가중']:.1f}, 중앙값 +{d['중앙값']:.1f}, p25 +{d['p25']:.1f}, p75 +{d['p75']:.1f}. 중앙값−인구가중 격차: 2010 {out.loc[2010,'중앙값']-out.loc[2010,'인구가중']:.1f}%p → 2025 {out.loc[2025,'중앙값']-out.loc[2025,'인구가중']:.1f}%p.")
open(os.path.join(HERE, "aging_desc.md"), "w", encoding="utf-8").write("\n".join(md)); print("\n".join(md))
plt.rcParams["font.family"] = ["Malgun Gothic", "sans-serif"]; plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
ax.fill_between(out.index, out.p25, out.p75, color="#9ecae1", alpha=.35, linewidth=0, label="시정촌 25~75분위")
ax.plot(out.index, out["중앙값"], color="#3182bd", lw=2, label="시정촌 중앙값")
ax.plot(out.index, out["인구가중"], color="#08306b", lw=2, label="인구가중 (전국)")
ax.plot(out.index, out["아파트표본_인구가중"], color="#08306b", lw=2, ls="--", label="인구가중, 아파트 표본")
for col, dy in [("중앙값", 0.6), ("인구가중", -0.9), ("아파트표본_인구가중", -0.9)]: ax.annotate(f"{out.loc[2025, col]:.1f}", (2025, out.loc[2025, col]), xytext=(4, dy * 6), textcoords="offset points", fontsize=8, color="#333")
ax.set_xlim(2010, 2025.8); ax.set_xticks(range(2010, 2026, 3)); ax.set_ylabel("65세 이상 비중 (%)"); ax.set_title("일본 시정촌 고령화율 추이, 2010~2025", fontsize=11, loc="left")
ax.grid(axis="y", color="#e5e5e5", lw=.8); ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, fontsize=8, loc="upper left")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "aging_trend.png")); print("aging_trend.png")
