# 인구 기준일 변경(2013년까지 3/31, 2014년부터 1/1) 점검 2: 표본을 자르지 않고 간격을 보정.
# 2013/14 경계를 걸치는 차분 구간(시작연도 ≤2013, 종료연도 ≥2014)은 실제 간격이 4.75년이므로 인구·연령비중의 차분값에 5/4.75를 곱해 5년치로 환산. 가격·소득은 역년 기준이라 그대로.
# 수준 회귀는 전국 공통 기준일 이동을 연도 FE가 흡수하므로 제외. 07_models_final.R과 같은 표본·사양, coefs_final.csv(원안)와 비교.
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
DEPS <- c(condo = "log_p_condo", house = "log_p_house", resi = "log_p_resi")
R <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate"); INC <- "log_income_pc_adj"
POPV <- c("log_pop", R); V <- c(DEPS, POPV, INC); K <- 5 / 4.75
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = V][year >= 2015]
d5[year - 5 <= 2013 & year >= 2014, (POPV) := lapply(.SD, `*`, K), .SDcols = POPV]
ld <- function(yrs) { e <- p[year %in% yrs]; o <- e[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))), lapply(.SD, diff)), by = muni_code, .SDcols = V]
  o[period == "2010_2015", (POPV) := lapply(.SD, `*`, K), .SDcols = POPV]; o }
ldA <- ld(c(2010, 2015, 2020, 2025)); ldB <- ld(c(2010, 2015, 2020))
SAMP <- list(A = list(d = d5, ld = ldA, inc = FALSE), B = list(d = d5[year <= 2024], ld = ldB, inc = FALSE), C = list(d = d5[year <= 2024], ld = ldB, inc = TRUE))
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (s in names(SAMP)) for (ver in c("ld5", "roll")) { S <- SAMP[[s]]; dat <- switch(ver, ld5 = S$ld, roll = S$d); fe <- switch(ver, ld5 = "period", roll = "year")
  for (d in names(DEPS)) {
    run <- function(tab, model, xs) { xs2 <- c(xs, if (S$inc) INC)
      m <- feols(as.formula(paste(DEPS[[d]], "~", paste(xs2, collapse = " + "), "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(m)
      for (t in rownames(ct)) add(sample = s, version = ver, dep = d, table = tab, model = model, term = t, coef = ct[t, 1], se = ct[t, 2], p = ct[t, 4], nobs = nobs(m)) }
    run("H1", "pop_only", "log_pop"); run("H1", "aging_only", "elderly_rate"); run("H1", "both", c("log_pop", "elderly_rate"))
    run("H3", "ref_middle", c("log_pop", unname(R[c("child", "youth", "elderly")]))); run("H3", "ref_child", c("log_pop", unname(R[c("youth", "middle", "elderly")])))
  } }
out <- rbindlist(rows); fwrite(out, "coefs_2014_interval.csv", bom = TRUE)
st <- function(pv) fifelse(pv < .01, "***", fifelse(pv < .05, "**", fifelse(pv < .1, "*", "")))
base <- fread("coefs_final.csv")[version != "level"]; cmp <- merge(base, out, by = c("sample", "version", "dep", "table", "model", "term"), suffixes = c("_base", "_adj"))
cmp[, chg := st(p_base) != st(p_adj)]; cat("차분 모형 계수", nrow(cmp), "개 중 유의수준 변경", sum(cmp$chg), "개\n"); print(cmp[chg == TRUE, .(sample, version, dep, model, term, coef_base, p_base, coef_adj, p_adj)])
cat("\n아파트 고령화율 (원안 → 보정):\n"); print(cmp[dep == "condo" & term == "elderly_rate" & model %in% c("aging_only", "both", "ref_middle"), .(sample, version, model, base = sprintf("%.4f%s", coef_base, st(p_base)), adj = sprintf("%.4f%s", coef_adj, st(p_adj)))])
cat("\n계수 변화 최대:\n"); print(cmp[term != INC][order(-abs(coef_adj - coef_base))][1:5, .(sample, version, dep, model, term, coef_base, coef_adj)])
