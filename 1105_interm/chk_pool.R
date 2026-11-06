suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
INC <- "log_income_pc_adj"; st <- function(pv) ifelse(pv < .01, "***", ifelse(pv < .05, "**", ifelse(pv < .1, "*", "")))
both <- !is.na(p$log_p_house) & !is.na(p$log_p_condo)
p[, log_p_eq := ifelse(both, 0.5 * log_p_house + 0.5 * log_p_condo, NA_real_)]           # 고정가중 1: 반반
p[, log_p_w := ifelse(both, 0.61 * log_p_house + 0.39 * log_p_condo, NA_real_)]          # 고정가중 2: 전국 거래 비중(단독 61%)
p[, log_p_resi_both := ifelse(both, log_p_resi, NA_real_)]                               # 합산 중앙값, 두 종류 다 있는 칸만
p[, log_p_house_both := ifelse(both, log_p_house, NA_real_)]; p[, log_p_condo_both := ifelse(both, log_p_condo, NA_real_)]
V <- c("log_p_house_both", "log_p_condo_both", "log_p_resi_both", "log_p_eq", "log_p_w", "log_pop", "elderly_rate", INC)
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = V][year >= 2015 & !is.na(get(INC))]
pi <- p[!is.na(get(INC))]
row <- function(lab, dep) { out <- c()
  for (k in 1:2) { dat <- if (k == 1) pi else d5; fe <- if (k == 1) "muni_code + year" else "year"
    m <- feols(as.formula(paste(dep, "~ log_pop + elderly_rate +", INC, "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(m)
    out <- c(out, sprintf("%7.4f (%.4f)%-3s n=%5d", ct["elderly_rate",1], ct["elderly_rate",2], st(ct["elderly_rate",4]), nobs(m))) }
  cat(sprintf("%-34s 수준 %s | 이동차분 %s\n", lab, out[1], out[2])) }
cat("== 소득 통제, 인구 통제 후 고령 계수. 표본 = 단독·아파트 둘 다 있는 칸 ==\n")
row("단독주택", "log_p_house_both"); row("아파트", "log_p_condo_both"); row("합산 중앙값(거래 풀)", "log_p_resi_both")
row("고정가중 반반", "log_p_eq"); row("고정가중 61:39", "log_p_w")
cat("\n== 적층(stacked): 단독·아파트 칸을 쌓고 시정촌×종류 FE + 연도×종류 FE, 공통 계수 (칸 단위 동일 가중) ==\n")
s <- rbind(pi[!is.na(log_p_house), .(muni_code, year, type = "house", y = log_p_house, log_pop, elderly_rate, inc = get(INC))],
           pi[!is.na(log_p_condo), .(muni_code, year, type = "condo", y = log_p_condo, log_pop, elderly_rate, inc = get(INC))])
for (lab in c("전체", "둘 다 있는 칸만")) { dat <- if (lab == "전체") s else s[paste(muni_code, year) %in% paste(p$muni_code, p$year)[both]]
  m <- feols(y ~ log_pop + elderly_rate + inc | muni_code^type + year^type, dat, cluster = ~muni_code); ct <- coeftable(m)
  cat(sprintf("%-20s 고령 %7.4f (%.4f)%s  인구 %.3f  n=%d\n", lab, ct["elderly_rate",1], ct["elderly_rate",2], st(ct["elderly_rate",4]), ct["log_pop",1], nobs(m))) }
cat("\n(참고) 둘 다 있는 칸:", sum(both), "/ 단독 있는 칸", sum(!is.na(p$log_p_house)), "/ 아파트 있는 칸", sum(!is.na(p$log_p_condo)), "\n")
