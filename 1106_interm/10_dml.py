"""1105_interm: Double Machine Learning (부분선형 모형, Chernozhukov et al. 2018) — 한국 쪽 절차와 동일하게.
Y = θ·D + g(X) + 시정촌FE + 연도FE.  D(관심변수)·X(통제변수)는 모형별로 아래 CONFIGS.
- 표본: 소득 있는 2010~2024 (표본 C). 종속변수 아파트·단독주택·주거용 건물.
- 고정효과: 분할(fold)별로 훈련·검증 표본 각각 안에서 시정촌·연도 이원 within 변환(불균형 패널이라 반복 평균 차감).
- 교차적합: 시정촌 단위 5-fold(같은 시정촌의 모든 연도는 같은 fold). 분할 시드 2개로 반복해 평균.
- 학습기 4종: Lasso(LassoCV), Random Forest, XGBoost, Gradient Boosting.
- θ = 잔차(Y)·잔차(D) 회귀, 표준오차는 시정촌 군집.
출력: dml_results.csv, dml_results.md
"""
import os, numpy as np, pandas as pd
from sklearn.linear_model import LassoCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
HERE = os.path.dirname(os.path.abspath(__file__))
INC = "log_income_pc_adj"
DEPS = {"condo": "log_p_condo", "house": "log_p_house", "resi": "log_p_resi"}
CONFIGS = {"H1_pop": ("log_pop", [INC]), "H1_eld": ("elderly_rate", [INC]), "H2_eld": ("elderly_rate", ["log_pop", INC])}
SEEDS = [1, 2]; K = 5
def learners(seed):
    return {"Lasso": LassoCV(cv=5, random_state=seed, max_iter=20000),
            "Random Forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=20, random_state=seed, n_jobs=-1),
            "XGBoost": XGBRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=1.0, random_state=seed, n_jobs=-1, verbosity=0),
            "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=seed)}

def within2(df, cols, tol=1e-10, it=100):
    """시정촌·연도 이원 within 변환 (불균형 패널: 수렴까지 교대 평균 차감)."""
    M = df[cols].to_numpy(dtype=float).copy()
    g1 = df["muni_code"].to_numpy(); g2 = df["year"].to_numpy()
    for _ in range(it):
        prev = M.copy()
        M -= pd.DataFrame(M).groupby(g1).transform("mean").to_numpy()
        M -= pd.DataFrame(M).groupby(g2).transform("mean").to_numpy()
        if np.abs(M - prev).max() < tol: break
    return M

def dml(df, dep, D, X, learner_fn, seed):
    munis = df.muni_code.unique(); rng = np.random.default_rng(seed); rng.shuffle(munis)
    fold_of = {m: i % K for i, m in enumerate(munis)}; folds = df.muni_code.map(fold_of).to_numpy()
    cols = [dep, D] + X; ry = np.empty(len(df)); rd = np.empty(len(df))
    for k in range(K):
        tr, te = folds != k, folds == k
        Wtr = within2(df[tr], cols); Wte = within2(df[te], cols)
        ytr, dtr, xtr = Wtr[:, 0], Wtr[:, 1], Wtr[:, 2:]; yte, dte, xte = Wte[:, 0], Wte[:, 1], Wte[:, 2:]
        my = learner_fn(seed).fit(xtr, ytr); md = learner_fn(seed).fit(xtr, dtr)
        ry[te] = yte - my.predict(xte); rd[te] = dte - md.predict(xte)
    theta = (rd * ry).sum() / (rd ** 2).sum()
    psi = rd * (ry - theta * rd); g = pd.Series(psi).groupby(df.muni_code.to_numpy()).sum().to_numpy()
    se = np.sqrt((g ** 2).sum()) / (rd ** 2).sum()
    return theta, se, len(df)

p = pd.read_csv(os.path.join(HERE, "..", "1105_interm", "panel_v5.csv"), dtype={"muni_code": str, "pref_code": str})
p = p[p[INC].notna()]
rows = []
for dk, dep in DEPS.items():
    d = p[p[dep].notna()][["muni_code", "year", dep, "log_pop", "elderly_rate", INC]].reset_index(drop=True)
    for ck, (D, X) in CONFIGS.items():
        for lname in learners(0):
            ths, ses = [], []
            for s in SEEDS:
                th, se, n = dml(d, dep, D, X, lambda seed, ln=lname: learners(seed)[ln], s); ths.append(th); ses.append(se)
            th, se = float(np.mean(ths)), float(np.mean(ses)); z = th / se
            from scipy.stats import norm; pval = 2 * norm.sf(abs(z))
            rows.append(dict(dep=dk, config=ck, D=D, X="+".join(X), learner=lname, coef=th, se=se, p=pval, nobs=n, coef_seed1=ths[0], coef_seed2=ths[1]))
            print(f"{dk:5s} {ck:7s} {lname:18s} θ={th:8.4f} ({se:.4f}) p={pval:.3f} n={n}  [seed별 {ths[0]:.4f}, {ths[1]:.4f}]", flush=True)
out = pd.DataFrame(rows); out.to_csv(os.path.join(HERE, "dml_results.csv"), index=False, encoding="utf-8-sig")

# ---- 표 ----
def cell(r):
    st = "***" if r.p < .01 else "**" if r.p < .05 else "*" if r.p < .1 else ""; dd = 3 if r.D == "log_pop" else 4
    return f"{r.coef:.{dd}f} ({r.se:.{dd}f}){st}".replace("-", "−")
DN = {"condo": "아파트", "house": "단독주택", "resi": "주거용 건물"}; CN = {"H1_pop": "H1 log 인구 (X: log 소득)", "H1_eld": "H1 고령화율 (X: log 소득)", "H2_eld": "H2 고령화율 (X: log 인구, log 소득)"}
md = ["# DML 결과 (일본, 소득 통제 표본 2010~2024)\n", "부분선형 모형 Y = θ·D + g(X) + 시정촌FE + 연도FE. 분할별 이원 within 변환, 시정촌 단위 5-fold 교차적합, 분할 시드 2회 평균. 칸 = θ (시정촌 군집 SE). *** 1%, ** 5%, * 10%.\n"]
for ck, cn in CN.items():
    md.append(f"## {cn}\n"); md.append("| 학습기 | " + " | ".join(DN[d] for d in DEPS) + " |"); md.append("|---|---|---|---|")
    for ln in learners(0):
        md.append(f"| {ln} | " + " | ".join(cell(out[(out.dep == d) & (out.config == ck) & (out.learner == ln)].iloc[0]) for d in DEPS) + " |")
    md.append("| 관측치 | " + " | ".join(f"{int(out[(out.dep == d) & (out.config == ck)].nobs.iloc[0]):,}" for d in DEPS) + " |\n")
open(os.path.join(HERE, "dml_results.md"), "w", encoding="utf-8").write("\n".join(md)); print("dml_results.md")
