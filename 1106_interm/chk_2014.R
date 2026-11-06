suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
INC <- "log_income_pc_adj"; st <- function(pv) ifelse(pv < .01, "***", ifelse(pv < .05, "**", ifelse(pv < .1, "*", "")))
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = c("log_p_condo", "log_p_house", "log_pop", "elderly_rate", INC)][year >= 2015]
show <- function(m, lab) { ct <- coeftable(m); cat(sprintf("%-44s 고령 %7.4f (%.4f)%-3s 인구 %5.3f  n=%d\n", lab, ct["elderly_rate",1], ct["elderly_rate",2], st(ct["elderly_rate",4]), ct["log_pop",1], nobs(m))) }
for (dep in c("log_p_condo", "log_p_house")) { cat("\n==", dep, "(식 2: 인구+고령화율, 소득 미통제) ==\n")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate | muni_code + year")), p, cluster = ~muni_code), "수준, 2010~2025 (기준일 혼재)")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate | muni_code + year")), p[year >= 2014], cluster = ~muni_code), "수준, 2014~2025 (1/1 기준일만)")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate | year")), d5, cluster = ~muni_code), "이동차분, 전체 11구간")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate | year")), d5[year >= 2019], cluster = ~muni_code), "이동차분, 2014→19 이후 7구간 (5년 정확)")
  cat("-- 소득 통제 --\n")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate +", INC, "| muni_code + year")), p[!is.na(get(INC))], cluster = ~muni_code), "수준, 2010~2024")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate +", INC, "| muni_code + year")), p[!is.na(get(INC)) & year >= 2014], cluster = ~muni_code), "수준, 2014~2024")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate +", INC, "| year")), d5[!is.na(get(INC))], cluster = ~muni_code), "이동차분, 10구간")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate +", INC, "| year")), d5[!is.na(get(INC)) & year >= 2019], cluster = ~muni_code), "이동차분, 2014→19 이후 6구간") }
