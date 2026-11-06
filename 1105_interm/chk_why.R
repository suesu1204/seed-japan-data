suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))
INC <- "log_income_pc_adj"; pi <- p[!is.na(get(INC))]
f <- function(dat, dep, lab, xs = c("log_pop", "elderly_rate", INC)) {
  m <- feols(as.formula(paste(dep, "~", paste(xs, collapse = "+"), "| muni_code + year")), dat, cluster = ~muni_code)
  ct <- coeftable(m); cat(sprintf("%-42s n=%6d  log_pop %6.3f (%.3f)  고령 %7.4f (%.4f)%s\n", lab, nobs(m), ct["log_pop",1], ct["log_pop",2], ct["elderly_rate",1], ct["elderly_rate",2],
    ifelse(ct["elderly_rate",4] < .01, "***", ifelse(ct["elderly_rate",4] < .05, "**", ifelse(ct["elderly_rate",4] < .1, "*", ""))))) }
cat("== 소득 통제, 수준 ==\n")
f(pi, "log_p_house", "단독주택, 전체 표본")
f(pi[!is.na(log_p_condo)], "log_p_house", "단독주택, 아파트 있는 칸만")
f(pi[!is.na(log_p_condo)], "log_p_condo", "아파트, 같은 칸")
f(pi[!is.na(log_p_house)], "log_p_land", "토지, 단독주택 있는 칸")

f(pi[!is.na(log_p_condo)], "log_p_land", "토지, 아파트 있는 칸")
cat("\n== 시정촌·연도 demean 후 log_pop vs 고령 비중 상관 ==\n")
for (s in c("house", "condo")) { d <- pi[!is.na(get(paste0("log_p_", s)))]
  r <- resid(feols(c(log_pop, elderly_rate) ~ 1 | muni_code + year, d)); cat(sprintf("%s 표본: within corr = %.3f, 시정촌 수 %d, 2010 인구 중앙값 %s\n", s, cor(r[,1], r[,2]), uniqueN(d$muni_code), format(median(d[year==2010, pop_total]), big.mark=",")))}
cat("\n== 단독주택: 규모 그룹별 (2010 인구: 1 <1만, 2 1~5만, 3 5~20만, 4 20만+) ==\n")
for (g in 1:4) f(pi[size_group == g], "log_p_house", paste0("단독주택 size_group ", g))
cat("\n== 단독주택: 고령화만 (인구 없이) vs 인구만 ==\n")
f(pi, "log_p_house", "단독주택 고령만+소득", c("elderly_rate", INC)); f(pi, "log_p_house", "단독주택 인구만+소득", c("log_pop", INC))
