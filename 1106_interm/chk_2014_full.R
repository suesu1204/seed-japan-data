# 인구 기준일 변경(2013년 3/31 → 2014년 1/1) 점검: 소득 통제 모형(표본 C, 2010~2024)을 2014년 이후 표본으로 재추정하여 전체 표본과 비교. 07_models_final.R과 같은 사양.
# 수준: 2014~2024. 이동차분: 2014→2019 이후 6구간. 비중첩 장기차분: 2015→2020 한 구간만 남음(2010→2015 제외).
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)][year <= 2024]
DEPS <- c(condo = "log_p_condo", house = "log_p_house", resi = "log_p_resi")
R <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate"); INC <- "log_income_pc_adj"
V <- c(DEPS, "log_pop", R, INC)
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = V][year >= 2015]
e <- p[year %in% c(2010, 2015, 2020)]; ld <- e[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))), lapply(.SD, diff)), by = muni_code, .SDcols = V]
SUB <- list(full = list(level = p, roll = d5, ld5 = ld), post2014 = list(level = p[year >= 2014], roll = d5[year >= 2019], ld5 = ld[period == "2015_2020"]))
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (s in names(SUB)) for (ver in c("level", "roll", "ld5")) { dat <- SUB[[s]][[ver]]; fe <- switch(ver, level = "muni_code + year", roll = "year", ld5 = "period")
  for (d in names(DEPS)) {
    run <- function(model, xs) { m <- feols(as.formula(paste(DEPS[[d]], "~", paste(c(xs, INC), collapse = " + "), "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(m)
      for (t in rownames(ct)) add(subsample = s, version = ver, dep = d, model = model, term = t, coef = ct[t, 1], se = ct[t, 2], p = ct[t, 4], nobs = nobs(m)) }
    run("pop_only", "log_pop"); run("aging_only", "elderly_rate"); run("both", c("log_pop", "elderly_rate"))
    run("ref_middle", c("log_pop", unname(R[c("child", "youth", "elderly")]))); run("ref_child", c("log_pop", unname(R[c("youth", "middle", "elderly")])))
  } }
out <- rbindlist(rows); fwrite(out, "coefs_2014_full.csv", bom = TRUE); cat("coefs_2014_full.csv", nrow(out), "행\n")
