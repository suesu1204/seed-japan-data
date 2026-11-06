suppressPackageStartupMessages({ library(data.table); library(fixest) })
tr <- fread("house_hed_trades.csv", colClasses = list(character = "muni_code")); tr[, my := paste(muni_code, year)]
m <- feols(ln_p ~ ln_floor + ln_land + age + I(age^2) + age_na + i(struct, ref = "木造") | my, tr)
cat("== 헤도닉 1단계 (거래", nobs(m), "건) ==\n"); print(round(coeftable(m)[, 1:2], 4))
fe <- as.data.table(fixef(m)$my, keep.rownames = TRUE); setnames(fe, c("my", "log_p_house_hed")); fe[, c("muni_code", "year") := tstrsplit(my, " ")]; fe[, year := as.integer(year)]
nn <- tr[, .(n_hed = .N, mean_age = mean(age), old_share = mean(age >= 30)), by = .(muni_code, year)]
p <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))
p <- merge(p, merge(fe[, .(muni_code, year, log_p_house_hed)], nn, by = c("muni_code", "year")), by = c("muni_code", "year"), all.x = TRUE)
p[is.na(n_hed) | n_hed < 5, log_p_house_hed := NA]
INC <- "log_income_pc_adj"; pi <- p[!is.na(get(INC))]
f <- function(dat, dep, lab, xs = c("log_pop", "elderly_rate", INC), ver = "level") {
  if (ver == "ld5") { ends <- dat[year %in% c(2010, 2015, 2020)][order(muni_code, year)]
    dat <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))), lapply(.SD, diff)), by = muni_code, .SDcols = c(dep, xs)]; fe <- "period" } else fe <- "muni_code + year"
  mm <- feols(as.formula(paste(dep, "~", paste(xs, collapse = "+"), "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(mm)
  st <- function(v) ifelse(ct[v,4] < .01, "***", ifelse(ct[v,4] < .05, "**", ifelse(ct[v,4] < .1, "*", "")))
  cat(sprintf("%-34s n=%6d  log_pop %6.3f (%.3f)%-3s 고령 %7.4f (%.4f)%s\n", lab, nobs(mm), ct["log_pop",1], ct["log_pop",2], st("log_pop"), ct["elderly_rate",1], ct["elderly_rate",2], st("elderly_rate"))) }
cat("\n== 2단계: 소득 통제, 수준 ==\n")
f(pi, "log_p_house", "단독주택 중앙값"); f(pi, "log_p_house_hed", "단독주택 헤도닉"); f(pi, "log_p_condo", "아파트 중앙값"); f(pi, "log_p_land", "토지 중앙값")
cat("\n== 2단계: 소득 통제, 5년 차분 ==\n")
f(pi, "log_p_house", "단독주택 중앙값", ver = "ld5"); f(pi, "log_p_house_hed", "단독주택 헤도닉", ver = "ld5"); f(pi, "log_p_condo", "아파트 중앙값", ver = "ld5")
cat("\n== 거래된 집의 구성이 인구·고령화에 따라 바뀌나 (종속 = 시정촌·연도 평균 연식 / 30년 이상 비중, 소득 통제 수준) ==\n")
f(pi[!is.na(log_p_house)], "mean_age", "평균 건물 연식(년)"); f(pi[!is.na(log_p_house)], "old_share", "30년 이상 비중")
cat("\n== within 상관 (시정촌·연도 demean) log_pop vs 고령 ==\n")
for (s in c("house", "condo")) { d <- pi[!is.na(get(paste0("log_p_", s)))]; r1 <- resid(feols(log_pop ~ 1 | muni_code + year, d)); r2 <- resid(feols(elderly_rate ~ 1 | muni_code + year, d))
  cat(sprintf("%s 표본: %.3f | within SD log_pop %.3f, 고령 %.2f\n", s, cor(r1, r2), sd(r1), sd(r2))) }
