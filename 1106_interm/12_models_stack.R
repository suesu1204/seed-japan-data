# 통합(적층) 추정: 아파트 행과 단독주택 행을 쌓아 한 회귀. 한국 방식과 동일(수준: 시정촌×유형 + 연도 FE, 차분: 구간/종료연도 FE, 시정촌 군집 SE).
# 표본·사양은 07_models_final.R과 같음. 출력 coefs_stack.csv (dep = "stack").
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
R <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate"); INC <- "log_income_pc_adj"
X <- c("log_pop", R, INC)
long <- rbindlist(list(p[, c(.(muni_code = muni_code, year = year, type = "condo", log_p = log_p_condo), .SD), .SDcols = X],
                       p[, c(.(muni_code = muni_code, year = year, type = "house", log_p = log_p_house), .SD), .SDcols = X]))[order(muni_code, type, year)]
long[, unit := paste(muni_code, type)]
V <- c("log_p", X)
d5 <- long[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = .(muni_code, type, unit), .SDcols = V][year >= 2015]
ld <- function(yrs) { e <- long[year %in% yrs]; e[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))), lapply(.SD, diff)), by = .(muni_code, type, unit), .SDcols = V] }
ldA <- ld(c(2010, 2015, 2020, 2025)); ldB <- ld(c(2010, 2015, 2020))
SAMP <- list(A = list(lv = long, d = d5, ld = ldA, inc = FALSE), B = list(lv = long[year <= 2024], d = d5[year <= 2024], ld = ldB, inc = FALSE), C = list(lv = long[year <= 2024], d = d5[year <= 2024], ld = ldB, inc = TRUE))
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (s in names(SAMP)) for (ver in c("level", "ld5", "roll")) { S <- SAMP[[s]]; dat <- switch(ver, level = S$lv, ld5 = S$ld, roll = S$d); fe <- switch(ver, level = "unit + year", ld5 = "period", roll = "year")
  run <- function(tab, model, xs) { xs2 <- c(xs, if (S$inc) INC)
    m <- feols(as.formula(paste("log_p ~", paste(xs2, collapse = " + "), "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(m)
    for (t in rownames(ct)) add(sample = s, version = ver, dep = "stack", table = tab, model = model, term = t, coef = ct[t, 1], se = ct[t, 2], p = ct[t, 4], nobs = nobs(m)) }
  run("H1", "pop_only", "log_pop"); run("H1", "aging_only", "elderly_rate"); run("H1", "both", c("log_pop", "elderly_rate"))
  run("H3", "ref_middle", c("log_pop", unname(R[c("child", "youth", "elderly")]))); run("H3", "ref_child", c("log_pop", unname(R[c("youth", "middle", "elderly")]))) }
out <- rbindlist(rows); fwrite(out, "coefs_stack.csv", bom = TRUE); cat("coefs_stack.csv", nrow(out), "행\n")
