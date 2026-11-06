# 1105_interm 최종 사양 (팀 결정 2026-11-06). 종속변수: 아파트·단독주택(·합산). 토지 제외.
# 표본 3종: A 2010~2025 소득 없음 / B 2010~2024 소득 없음 / C 2010~2024 소득 통제. 각각 수준(시정촌+연도 FE), 비중첩 5년 장기차분(A: 2010→15·15→20·20→25, B·C: 앞 2구간; 구간 FE), 5년 이동차분(t−5→t, 종료연도 FE; A 11구간, B·C 10구간).
# 모형: H1 인구만·고령화만·둘 다, H3 4연령(중장년 기준) + 유소년 기준(고령 계수 = 교환효과).
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v5_min1.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
DEPS <- c(condo = "log_p_condo", house = "log_p_house", resi = "log_p_resi")
R <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate"); INC <- "log_income_pc_adj"
V <- c(DEPS, "log_pop", R, INC)
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = V][year >= 2015]
ld <- function(yrs) { e <- p[year %in% yrs]; e[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))), lapply(.SD, diff)), by = muni_code, .SDcols = V] }
ldA <- ld(c(2010, 2015, 2020, 2025)); ldB <- ld(c(2010, 2015, 2020))
SAMP <- list(A = list(lv = p, d = d5, ld = ldA, inc = FALSE), B = list(lv = p[year <= 2024], d = d5[year <= 2024], ld = ldB, inc = FALSE), C = list(lv = p[year <= 2024], d = d5[year <= 2024], ld = ldB, inc = TRUE))
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (s in names(SAMP)) for (ver in c("level", "ld5", "roll")) { S <- SAMP[[s]]; dat <- switch(ver, level = S$lv, ld5 = S$ld, roll = S$d); fe <- switch(ver, level = "muni_code + year", ld5 = "period", roll = "year")
  for (d in names(DEPS)) {
    run <- function(tab, model, xs) { xs2 <- c(xs, if (S$inc) INC)
      m <- feols(as.formula(paste(DEPS[[d]], "~", paste(xs2, collapse = " + "), "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(m)
      for (t in rownames(ct)) add(sample = s, version = ver, dep = d, table = tab, model = model, term = t, coef = ct[t, 1], se = ct[t, 2], p = ct[t, 4], nobs = nobs(m)) }
    run("H1", "pop_only", "log_pop"); run("H1", "aging_only", "elderly_rate"); run("H1", "both", c("log_pop", "elderly_rate"))
    run("H3", "ref_middle", c("log_pop", unname(R[c("child", "youth", "elderly")]))); run("H3", "ref_child", c("log_pop", unname(R[c("youth", "middle", "elderly")])))
  } }
out <- rbindlist(rows); fwrite(out, "coefs_final_min1.csv", bom = TRUE); cat("coefs_final.csv", nrow(out), "행\n")
print(dcast(out[table == "H1" & model == "both" & term == "elderly_rate"], sample + version ~ dep, value.var = "coef"))
