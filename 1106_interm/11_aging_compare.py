"""한일 고령화 수준 비교용 일본 쪽 표·그림. 고령화율 = 65세 이상 인구 / 총인구 × 100.
출력: aging_level_JP.csv (한국이 같은 열로 채울 양식), aging_level_template_KR.csv, aging_level_JP.md, aging_dist_JP.png
열 정의: aging_popweighted = Σ65세 이상 / Σ총인구 × 100 (전국 인구가중), aging_mean = 지역 단순평균, aging_p5/p25/median/p75/p95 = 지역 분포 분위수, n_regions = 지역 수.
"""
import os, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
p = pd.read_csv(os.path.join(HERE, "..", "1105_interm", "panel_v5.csv"), dtype={"muni_code": str}, usecols=["muni_code", "year", "pop_total", "elderly_rate", "log_p_condo"])
def stats(g, label):
    return pd.Series({"country": "JP", "sample": label, "aging_popweighted": np.average(g.elderly_rate, weights=g.pop_total), "aging_mean": g.elderly_rate.mean(),
                      "aging_p5": g.elderly_rate.quantile(.05), "aging_p25": g.elderly_rate.quantile(.25), "aging_median": g.elderly_rate.median(),
                      "aging_p75": g.elderly_rate.quantile(.75), "aging_p95": g.elderly_rate.quantile(.95), "n_regions": len(g)})
rows = [stats(g, "all").rename(y) for y, g in p.groupby("year")] + [stats(g, "condo_sample").rename(y) for y, g in p[p.log_p_condo.notna()].groupby("year")]
out = pd.DataFrame(rows).rename_axis("year").reset_index(); out = out[["country", "sample", "year"] + [c for c in out.columns if c.startswith("aging") or c == "n_regions"]]
out.round(2).to_csv(os.path.join(HERE, "aging_level_JP.csv"), index=False, encoding="utf-8-sig")
tpl = out[out["sample"] == "all"].copy(); tpl["country"] = "KR"; tpl["sample"] = "all"
for c in tpl.columns[3:]: tpl[c] = ""
tpl.to_csv(os.path.join(HERE, "aging_level_template_KR.csv"), index=False, encoding="utf-8-sig")
a = out[out["sample"] == "all"].set_index("year")
md = ["# 일본 고령화율 수준 (65세 이상 비중, %), 1,741 시정촌\n", "인구가중 = Σ65세 이상 ÷ Σ총인구. 분위수는 시정촌 분포. 5·95분위는 한일 공통 범위 산정용.\n",
      "| 연도 | 인구가중 | 단순평균 | p5 | p25 | 중앙값 | p75 | p95 |", "|---|---|---|---|---|---|---|---|"]
for y, r in a.iterrows(): md.append(f"| {y} | {r.aging_popweighted:.1f} | {r.aging_mean:.1f} | {r.aging_p5:.1f} | {r.aging_p25:.1f} | {r.aging_median:.1f} | {r.aging_p75:.1f} | {r.aging_p95:.1f} |")
pooled = p.elderly_rate.quantile([.05, .95]); md.append(f"\n전 기간(2010~2025) 시정촌·연도 풀링 5·95분위: {pooled[.05]:.1f}~{pooled[.95]:.1f}%. 연도별 5분위 최소 {a.aging_p5.min():.1f}(2010), 95분위 최대 {a.aging_p95.max():.1f}(2025).")
open(os.path.join(HERE, "aging_level_JP.md"), "w", encoding="utf-8").write("\n".join(md)); print("\n".join(md))
# ---- 분포 그림: 2010·2015·2020·2025 시정촌 고령화율 밀도 ----
plt.rcParams["font.family"] = ["Malgun Gothic", "sans-serif"]; plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
cols = {2010: "#c6dbef", 2015: "#6baed6", 2020: "#2171b5", 2025: "#08306b"}; grid = np.linspace(0, 65, 400)
for y, c in cols.items():
    v = p[p.year == y].elderly_rate.to_numpy(); bw = 1.06 * v.std() * len(v) ** (-1 / 5)
    dens = np.exp(-0.5 * ((grid[:, None] - v[None, :]) / bw) ** 2).sum(axis=1) / (len(v) * bw * np.sqrt(2 * np.pi))
    ax.plot(grid, dens, color=c, lw=2, label=f"{y}년 (중앙값 {np.median(v):.1f}%)")
ax.set_xlim(0, 65); ax.set_xlabel("시정촌 고령화율 (65세 이상 비중, %)"); ax.set_ylabel("밀도"); ax.set_title("일본 시정촌 고령화율 분포, 2010·2015·2020·2025", fontsize=11, loc="left")
ax.grid(axis="y", color="#e5e5e5", lw=.8); ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "aging_dist_JP.png")); print("aging_dist_JP.png")
