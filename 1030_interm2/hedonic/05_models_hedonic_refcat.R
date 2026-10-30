# 헤도닉 기준 범주 3종 (유소년/청년/고령 기준). 1030 사양, 종속변수 헤도닉 지수. 출력: coefs_hedonic_refcat.csv (4기준 × 2종속 × 2버전 × 6행 = 96행)
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../panel_v2.csv", colClasses = list(character = c("muni_code", "pref_code")))
DEPS <- c(land = "log_p_land_hed", condo = "log_p_condo_hed"); RATES <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate")
ends <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]), lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", RATES)]
rows <- list()
for (version in c("level", "ld5")) { dat <- if (version == "level") p else ld; fe <- if (version == "level") "muni_code + pref_code^year" else "pref_code^period"
  for (d in names(DEPS)) for (ref in c("middle", "child", "youth", "elderly")) {
    xs <- c("log_pop", unname(RATES[names(RATES) != ref]))
    m <- feols(as.formula(paste(DEPS[[d]], "~", paste(xs, collapse = " + "), "|", fe)), data = dat, cluster = ~muni_code)
    ct <- coeftable(m); b <- coef(m); V <- vcov(m)
    add <- function(term, est, se) rows[[length(rows) + 1]] <<- data.table(table = "H2", version = version, dep = d, ref = ref, term = term, coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = nobs(m))
    for (term in rownames(ct)) add(term, ct[term, 1], ct[term, 2])
    cvec0 <- setNames(rep(0, length(b)), names(b))
    for (nm in c("child_plus_elderly", "child_minus_elderly")) { cvec <- cvec0
      if ("child_rate" %in% names(b)) cvec["child_rate"] <- 1
      if ("elderly_rate" %in% names(b)) cvec["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
      add(nm, sum(cvec * b), sqrt(as.numeric(t(cvec) %*% V %*% cvec))) }
  } }
out <- rbindlist(rows); stopifnot(nrow(out) == 96); fwrite(out, "coefs_hedonic_refcat.csv", bom = TRUE); cat("coefs_hedonic_refcat.csv", nrow(out), "행\n")
