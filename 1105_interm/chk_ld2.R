suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
st <- function(pv) ifelse(pv < .01, "***", ifelse(pv < .05, "**", ifelse(pv < .1, "*", "")))
show <- function(m, lab, a = "log_pop", b = "elderly_rate") { ct <- coeftable(m); cat(sprintf("%-40s n=%6d  인구 %6.3f (%.3f)%-3s 고령 %7.4f (%.4f)%s\n", lab, nobs(m), ct[a,1], ct[a,2], st(ct[a,4]), ct[b,1], ct[b,2], st(ct[b,4]))) }
p[, `:=`(eld_l5 = shift(elderly_rate, 5), pop_l5 = shift(log_pop, 5), d5_eld = elderly_rate - shift(elderly_rate, 5), d5_pop = log_pop - shift(log_pop, 5)), by = muni_code]
for (s in c("house", "condo")) { dep <- paste0("log_p_", s); cat("\n=====", s, "(소득 없음) =====\n")
  yrs <- c(2010, 2015, 2020, 2025); ends <- p[year %in% yrs & !is.na(get(dep))]
  ld <- ends[, { k <- which(diff(year) == 5); .(period = paste0(year[k], "_", year[k+1]), dy = get(dep)[k+1] - get(dep)[k], dpop = log_pop[k+1] - log_pop[k], deld = elderly_rate[k+1] - elderly_rate[k]) }, by = muni_code][!is.na(dy)]
  for (pr in sort(unique(ld$period))) show(feols(dy ~ dpop + deld, as.data.frame(ld)[ld$period == pr, ], cluster = ~muni_code), paste("5년 차분", pr), "dpop", "deld")
  cat("-- 수준 FE에 5년 전 값 추가 (현재 + 시차 = 누적 효과) --\n")
  m <- feols(as.formula(paste(dep, "~ log_pop + pop_l5 + elderly_rate + eld_l5 | muni_code + year")), p, cluster = ~muni_code); ct <- coeftable(m)
  cat(sprintf("현재 고령 %7.4f (%.4f)%s  5년 전 고령 %7.4f (%.4f)%s  합 %7.4f  | 인구 현재 %.3f 5년 전 %.3f  n=%d\n", ct["elderly_rate",1], ct["elderly_rate",2], st(ct["elderly_rate",4]), ct["eld_l5",1], ct["eld_l5",2], st(ct["eld_l5",4]), ct["elderly_rate",1] + ct["eld_l5",1], ct["log_pop",1], ct["pop_l5",1], nobs(m)))
  cat("-- 수준 FE, 5년 변화량을 설명변수로 (연간 패널, 모든 해) --\n")
  show(feols(as.formula(paste(dep, "~ d5_pop + d5_eld | muni_code + year")), p, cluster = ~muni_code), "가격 수준 ~ 지난 5년 인구·고령 변화", "d5_pop", "d5_eld") }
