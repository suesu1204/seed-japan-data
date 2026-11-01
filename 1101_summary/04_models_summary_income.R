# 1101_summary 소득 통제판. 01_models_summary.R 과 같은 모형에 log 1인당 소득(보간, log_income_pc_adj) 추가.
# 표본: 소득 있는 행 = 2010~2024 (2025년 소득 없음). 5년 차분은 2010→15, 15→20 두 구간. 고정효과 2종(지역+연도 / 지역+현×연도).
# 입력 ../1031_interm/panel_v4.csv  출력 coefs_summary_income.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1031_interm/panel_v4.csv", colClasses = list(character = c("muni_code", "pref_code")))[!is.na(log_income_pc_adj)]
stopifnot(max(p$year) == 2024)
DEPS <- c(land = "log_p_land", condo = "log_p_condo", land_hedA = "log_p_land_hedA_nofloor", condo_hedA = "log_p_condo_hed")
RATES <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate"); INC <- "log_income_pc_adj"
ends <- p[year %in% c(2010, 2015, 2020)][order(muni_code, year)]
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]), lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", RATES, INC)]
FE <- list(level = c(year = "muni_code + year", prefyear = "muni_code + pref_code^year"), ld5 = c(year = "period", prefyear = "pref_code^period"))
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (version in c("level", "ld5")) { dat <- if (version == "level") p else ld
  for (fe in c("year", "prefyear")) for (d in names(DEPS)) {
    run <- function(tab, model, xs) {
      m <- feols(as.formula(paste(DEPS[[d]], "~", paste(c(xs, INC), collapse = " + "), "|", FE[[version]][[fe]])), dat, cluster = ~muni_code); ct <- coeftable(m)
      for (t in rownames(ct)) add(table = tab, version = version, fe = fe, dep = d, model = model, term = t, coef = ct[t, 1], se_cluster = ct[t, 2], p = ct[t, 4], nobs = nobs(m))
      if (tab == "H2") { b <- coef(m); V <- vcov(m); for (nm in c("child_plus_elderly", "child_minus_elderly")) { cv <- setNames(rep(0, length(b)), names(b))
        if ("child_rate" %in% names(b)) cv["child_rate"] <- 1; if ("elderly_rate" %in% names(b)) cv["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
        est <- sum(cv * b); se <- sqrt(as.numeric(t(cv) %*% V %*% cv)); add(table = tab, version = version, fe = fe, dep = d, model = model, term = nm, coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = nobs(m)) } } }
    run("H1", "pop_only", "log_pop"); run("H1", "aging_only", "elderly_rate"); run("H1", "both", c("log_pop", "elderly_rate"))
    for (ref in names(RATES)) run("H2", paste0("ref_", ref), c("log_pop", unname(RATES[names(RATES) != ref])))
    for (g in names(RATES)) run("H2-1", g, c("log_pop", RATES[[g]]))
  } }
out <- rbindlist(rows); fwrite(out, "coefs_summary_income.csv", bom = TRUE); cat("coefs_summary_income.csv", nrow(out), "행\n")
