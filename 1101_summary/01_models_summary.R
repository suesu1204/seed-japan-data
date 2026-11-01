# 1101_summary. 정리본용 통합 재추정. 소득 없음, 2010~2025. 종속변수 4 × 버전 2(수준/5년 차분) × 고정효과 2(지역+연도 / 지역+현×연도).
# 모형: H1 인구만·고령화만·둘 다, H2 기준 4종(합·차 포함), H2-1 비중 하나씩 4종. 기존 결과(1030_interm2·3)와 동일한 사양의 재추정이라 숫자가 같아야 함.
# 입력 ../1031_interm/panel_v4.csv  출력 coefs_summary.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1031_interm/panel_v4.csv", colClasses = list(character = c("muni_code", "pref_code")))
DEPS <- c(land = "log_p_land", condo = "log_p_condo", land_hedA = "log_p_land_hedA_nofloor", condo_hedA = "log_p_condo_hed")
RATES <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate")
ends <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]), lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", RATES)]
FE <- list(level = c(year = "muni_code + year", prefyear = "muni_code + pref_code^year"), ld5 = c(year = "period", prefyear = "pref_code^period"))
rows <- list()
add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (version in c("level", "ld5")) { dat <- if (version == "level") p else ld
  for (fe in c("year", "prefyear")) for (d in names(DEPS)) {
    run <- function(tab, model, xs) {
      m <- feols(as.formula(paste(DEPS[[d]], "~", paste(xs, collapse = " + "), "|", FE[[version]][[fe]])), dat, cluster = ~muni_code); ct <- coeftable(m)
      for (t in rownames(ct)) add(table = tab, version = version, fe = fe, dep = d, model = model, term = t, coef = ct[t, 1], se_cluster = ct[t, 2], p = ct[t, 4], nobs = nobs(m))
      if (tab == "H2") { b <- coef(m); V <- vcov(m); for (nm in c("child_plus_elderly", "child_minus_elderly")) { cv <- setNames(rep(0, length(b)), names(b))
        if ("child_rate" %in% names(b)) cv["child_rate"] <- 1; if ("elderly_rate" %in% names(b)) cv["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
        est <- sum(cv * b); se <- sqrt(as.numeric(t(cv) %*% V %*% cv)); add(table = tab, version = version, fe = fe, dep = d, model = model, term = nm, coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = nobs(m)) } } }
    run("H1", "pop_only", "log_pop"); run("H1", "aging_only", "elderly_rate"); run("H1", "both", c("log_pop", "elderly_rate"))
    for (ref in names(RATES)) run("H2", paste0("ref_", ref), c("log_pop", unname(RATES[names(RATES) != ref])))
    for (g in names(RATES)) run("H2-1", g, c("log_pop", RATES[[g]]))
  } }
out <- rbindlist(rows); fwrite(out, "coefs_summary.csv", bom = TRUE); cat("coefs_summary.csv", nrow(out), "행\n")
print(out[table == "H1" & model == "both" & term == "elderly_rate", .(version, fe, dep, coef = round(coef, 4), se = round(se_cluster, 4), nobs)])
