suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))
st <- function(pv) ifelse(pv < .01, "***", ifelse(pv < .05, "**", ifelse(pv < .1, "*", "")))
show <- function(m, lab) { ct <- coeftable(m); cat(sprintf("%-46s n=%6d  log_pop %6.3f (%.3f)%-3s 고령 %7.4f (%.4f)%s\n", lab, nobs(m), ct[1,1], ct[1,2], st(ct[1,4]), ct[2,1], ct[2,2], st(ct[2,4]))) }
for (s in c("house", "condo")) { dep <- paste0("log_p_", s); cat("\n=====", s, "(소득 없음) =====\n")
  yrs <- c(2010, 2015, 2020, 2025); ends <- p[year %in% yrs & !is.na(get(dep))][order(muni_code, year)]
  ld <- ends[, { k <- which(diff(year) == 5); .(period = paste0(year[k], "_", year[k+1]), dy = get(dep)[k+1] - get(dep)[k], dpop = log_pop[k+1] - log_pop[k], deld = elderly_rate[k+1] - elderly_rate[k]) }, by = muni_code]
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate | muni_code + year")), p, cluster = ~muni_code), "수준 FE, 연간 전체")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate | muni_code + year")), p[muni_code %in% unique(ld$muni_code)], cluster = ~muni_code), "수준 FE, 연간, 차분 표본 시정촌만")
  show(feols(as.formula(paste(dep, "~ log_pop + elderly_rate | muni_code + year")), p[year %in% yrs], cluster = ~muni_code), "수준 FE, 5년 간격 4시점만")
  show(feols(dy ~ dpop + deld | period, ld, cluster = ~muni_code), "5년 차분 (전 구간)")
  ld <- ld[!is.na(dy)]
  for (pr in sort(unique(ld$period))) { sub <- as.data.frame(ld)[ld$period == pr, ]; show(feols(dy ~ dpop + deld, sub, cluster = ~muni_code), paste("5년 차분", pr)) }
  # 연간 가격 잡음: 시정촌별로 연도 추세 제거 후 잔차 SD vs 5년 변화 SD
  r <- resid(feols(as.formula(paste(dep, "~ 1 | muni_code + year")), p, cluster = ~muni_code)); cat(sprintf("가격 within SD(연간) %.3f | 5년 변화 SD %.3f | 고령 5년 변화 SD %.2f, 연간 within SD %.2f\n", sd(r), sd(ld$dy), sd(ld$deld), sd(resid(feols(elderly_rate ~ 1 | muni_code + year, p[!is.na(get(dep))])))))
  # 3년 평균 끝점으로 차분 (avg3 열이 있으면)
  if (s %in% c("condo")) { ends2 <- p[year %in% yrs & !is.na(get(paste0("avg3_", dep)))][order(muni_code, year)]
    ld2 <- ends2[, { k <- which(diff(year) == 5); .(period = paste0(year[k], "_", year[k+1]), dy = get(paste0("avg3_", dep))[k+1] - get(paste0("avg3_", dep))[k], dpop = log_pop[k+1] - log_pop[k], deld = elderly_rate[k+1] - elderly_rate[k]) }, by = muni_code]
    ld2 <- ld2[!is.na(dy)]; show(feols(dy ~ dpop + deld | period, ld2, cluster = ~muni_code), "5년 차분, 끝점 3년 평균") } }
