"""H1 임시 추정 (2026-10-15). 일본 전국 시정촌 패널, 2010~2025.

입력: ../jp_pop_preprocessed.csv, ../torihiki_preprocessed.csv  (year, muni_code로 합침)
출력: h1_coefs.csv    모형별 계수표 (model, dep, sample, term, coef, se_cluster, p_cluster, se_dk, p_dk, nobs, n_muni, r2_within)
      h1_results.txt  계수표 + 검정 결과 (Pesaran CD, 하우스만, Fisher ADF)

모형
 1. FE   : log_med ~ aging_rate + log_total_pop + 시정촌FE + 연도FE.  표본 전국/과소/비과소.  전국은 aging×kaso 상호작용 모형 추가
 2. 검정 : Pesaran CD (FE 전국 잔차), 하우스만 (FE vs RE, 연도더미 포함)
 3. FD   : Δlog_med ~ Δaging_rate + Δlog_total_pop + 연도FE  (연속 두 해 모두 있는 경우만)
 4. ADF  : Fisher형 패널 ADF (시정촌별 ADF p값 합산, 상수항, 시차 1). 가격은 16년 전부 있는 시정촌만
표준오차: se_cluster = 시정촌 군집, se_dk = Driscoll–Kraay (횡단면 의존성 보정)
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from linearmodels.panel import PanelOLS, RandomEffects

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(HERE)
DEPS = {"land": "log_med_land", "landbldg": "log_med_landbldg"}
X0 = ["aging_rate", "log_total_pop"]

pop = pd.read_csv(os.path.join(UP, "jp_pop_preprocessed.csv"), dtype={"muni_code": str})
tor = pd.read_csv(os.path.join(UP, "torihiki_preprocessed.csv"), dtype={"muni_code": str})
df = pop.merge(tor, on=["year", "muni_code"], how="inner")
assert len(df) == len(pop) == len(tor) == 1741 * 16
df["aging_x_kaso"] = df.aging_rate * df.kaso_dummy
df = df.set_index(["muni_code", "year"]).sort_index()

rows, log = [], []


def say(s=""):
    print(s)
    log.append(s)


def record(model, dep, sample, res_cl, res_dk, terms):
    for t in terms:
        rows.append(dict(model=model, dep=dep, sample=sample, term=t,
                         coef=res_cl.params[t], se_cluster=res_cl.std_errors[t], p_cluster=res_cl.pvalues[t],
                         se_dk=res_dk.std_errors[t], p_dk=res_dk.pvalues[t],
                         nobs=int(res_cl.nobs), n_muni=int(res_cl.entity_info["total"]), r2_within=res_cl.rsquared_within))


def fit_fe(data, dep, xcols, entity=True):
    d = data[[dep] + xcols].dropna()
    mod = PanelOLS(d[dep], d[xcols], entity_effects=entity, time_effects=True)
    return mod.fit(cov_type="clustered", cluster_entity=True), mod.fit(cov_type="kernel")


# ---------- 1. FE ----------
fe_resid = {}
for k, dep in DEPS.items():
    for sample, sub in [("all", df), ("kaso", df[df.kaso_dummy == 1]), ("nonkaso", df[df.kaso_dummy == 0])]:
        cl, dk = fit_fe(sub, dep, X0)
        record("FE", k, sample, cl, dk, X0)
        if sample == "all":
            fe_resid[k] = cl.resids
    cl, dk = fit_fe(df, dep, X0 + ["aging_x_kaso"])
    record("FE_interact", k, "all", cl, dk, X0 + ["aging_x_kaso"])

# ---------- 2. 검정 ----------
tests = []


def pesaran_cd(resid):
    """불균형 패널용: CD = sqrt(1/n_pairs) * Σ_{i<j} sqrt(T_ij) * rho_ij  ~ N(0,1)"""
    R = resid.unstack(level=0)  # T x N
    rho = R.corr(min_periods=3).to_numpy()
    nn = R.notna().to_numpy().astype(float)
    T = nn.T @ nn
    iu = np.triu_indices(rho.shape[0], 1)
    r, t = rho[iu], T[iu]
    ok = ~np.isnan(r)
    cd = np.sqrt(1 / ok.sum()) * np.sum(np.sqrt(t[ok]) * r[ok])
    return cd, 2 * (1 - stats.norm.cdf(abs(cd))), int(ok.sum()), float(np.nanmean(r))


for k, dep in DEPS.items():
    cd, p, npairs, mean_rho = pesaran_cd(fe_resid[k])
    tests.append(f"[Pesaran CD] {k}: CD = {cd:.2f}, p = {p:.3g}, 시정촌 쌍 {npairs:,}개, 평균 잔차상관 {mean_rho:.3f}")

    # 하우스만: FE(시정촌FE + 연도더미) vs RE(연도더미), 비강건 분산
    d = df[[dep] + X0].dropna()
    yd = pd.get_dummies(d.index.get_level_values("year"), prefix="y", drop_first=True, dtype=float)
    yd.index = d.index
    X = pd.concat([d[X0], yd], axis=1)
    fe = PanelOLS(d[dep], X, entity_effects=True).fit(cov_type="unadjusted")
    re = RandomEffects(d[dep], X.assign(const=1.0)).fit(cov_type="unadjusted")
    b = fe.params[X0] - re.params[X0]
    V = fe.cov.loc[X0, X0] - re.cov.loc[X0, X0]
    H = float(b.T @ np.linalg.pinv(V.to_numpy()) @ b)
    tests.append(f"[Hausman] {k}: H = {H:.1f}, df = 2, p = {1 - stats.chi2.cdf(H, 2):.3g}  "
                 f"(FE aging {fe.params['aging_rate']:.4f} vs RE aging {re.params['aging_rate']:.4f})")

# ---------- 3. FD ----------
prev = df.groupby(level=0).shift(1)
yr = df.index.get_level_values("year").to_series(index=df.index)
consec = (yr - yr.groupby(level=0).shift(1)) == 1
fd = (df[list(DEPS.values()) + X0] - prev[list(DEPS.values()) + X0])[consec]
fd.columns = ["d_" + c for c in fd.columns]
fd["d_aging_x_kaso"] = fd.d_aging_rate * df.kaso_dummy[consec]
for k, dep in DEPS.items():
    xs = ["d_aging_rate", "d_log_total_pop"]
    for sample, sub in [("all", fd), ("kaso", fd[df.kaso_dummy[consec] == 1]), ("nonkaso", fd[df.kaso_dummy[consec] == 0])]:
        cl, dk = fit_fe(sub, "d_" + dep, xs, entity=False)
        record("FD", k, sample, cl, dk, xs)
    cl, dk = fit_fe(fd, "d_" + dep, xs + ["d_aging_x_kaso"], entity=False)
    record("FD_interact", k, "all", cl, dk, xs + ["d_aging_x_kaso"])


# ---------- 4. Fisher ADF ----------
def fisher_adf(series_by_muni, label):
    ps = []
    for _, s in series_by_muni:
        s = s.dropna()
        if len(s) < 12:
            continue
        ps.append(adfuller(s.to_numpy(), maxlag=1, autolag=None, regression="c")[1])
    ps = np.clip(np.array(ps), 1e-300, 1)
    P = -2 * np.log(ps).sum()
    return (f"[Fisher ADF] {label}: 시정촌 {len(ps):,}개, χ²({2 * len(ps)}) = {P:,.0f}, "
            f"p = {1 - stats.chi2.cdf(P, 2 * len(ps)):.3g}, 개별 p<0.05 비율 {(ps < 0.05).mean():.1%}")


for col, label in [("log_med_land", "수준 log_med_land"), ("log_med_landbldg", "수준 log_med_landbldg"), ("aging_rate", "수준 aging_rate")]:
    full = df[col].groupby(level=0).filter(lambda s: s.notna().all())
    tests.append(fisher_adf(full.groupby(level=0), label))
    dcol = full.groupby(level=0).diff()
    tests.append(fisher_adf(dcol.groupby(level=0), "1차차분 Δ" + col))

# ---------- 출력 ----------
coefs = pd.DataFrame(rows)
coefs.to_csv(os.path.join(HERE, "h1_coefs.csv"), index=False, encoding="utf-8-sig")
assert coefs.query("model=='FE' and term=='aging_rate'").nobs.sum() == 2 * coefs.query("model=='FE' and sample=='all' and term=='aging_rate'").nobs.sum()

pd.set_option("display.width", 200)
say("=== 계수표 (coef: 고령화율 1%p 상승 시 log 가격 변화; se_cluster 시정촌 군집, se_dk Driscoll-Kraay) ===")
say(coefs.round(4).to_string(index=False))
say()
say("=== 검정 ===")
for t in tests:
    say(t)
say()
say("주의: T=16이라 ADF 검정력 낮음. 공적분 검정(Kao/Pedroni)은 파이썬 미구현으로 생략, FD로 대체.")
with open(os.path.join(HERE, "h1_results.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log))
