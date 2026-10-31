# 분석 회귀 (1030 사양: 시정촌 + 현×연도 / 현×구간, 시정촌 군집). 종속변수: land_B, condo_B, land_A_nofloor
# 표: H1(3), H2 기준 4종(합·차 포함), H2-1(4). 출력: coefs_B.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v3.csv", colClasses = list(character = c("muni_code", "pref_code")))
DEPS <- c(land_B = "log_p_land_hedB", condo_B = "log_p_condo_hedB", land_A_nofloor = "log_p_land_hedA_nofloor")
RATES <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate")
ends <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]), lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", RATES)]
rows <- list()
add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (version in c("level", "ld5")) { dat <- if (version == "level") p else ld; fe <- if (version == "level") "muni_code + pref_code^year" else "pref_code^period"
  for (d in names(DEPS)) {
    run <- function(tab, model, ref, xs) { m <- feols(as.formula(paste(DEPS[[d]], "~", paste(xs, collapse = " + "), "|", fe)), data = dat, cluster = ~muni_code)
      ct <- coeftable(m); for (term in rownames(ct)) add(table = tab, version = version, dep = d, model = model, ref = ref, term = term, coef = ct[term, 1], se_cluster = ct[term, 2], p = ct[term, 4], nobs = nobs(m))
      if (tab == "H2") { b <- coef(m); V <- vcov(m); for (nm in c("child_plus_elderly", "child_minus_elderly")) { cvec <- setNames(rep(0, length(b)), names(b))
        if ("child_rate" %in% names(b)) cvec["child_rate"] <- 1; if ("elderly_rate" %in% names(b)) cvec["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
        est <- sum(cvec * b); se <- sqrt(as.numeric(t(cvec) %*% V %*% cvec)); add(table = tab, version = version, dep = d, model = model, ref = ref, term = nm, coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = nobs(m)) } } }
    run("H1", "pop_only", "", "log_pop"); run("H1", "aging_only", "", "elderly_rate"); run("H1", "both", "", c("log_pop", "elderly_rate"))
    for (ref in c("middle", "child", "youth", "elderly")) run("H2", paste0("ref_", ref), ref, c("log_pop", unname(RATES[names(RATES) != ref])))
    for (m in names(RATES)) run("H2-1", m, "", c("log_pop", RATES[[m]]))
  } }
out <- rbindlist(rows); stopifnot(nrow(out) == 3 * 2 * (4 + 4 * 6 + 8)); fwrite(out, "coefs_B.csv", bom = TRUE); cat("coefs_B.csv", nrow(out), "행\n")
