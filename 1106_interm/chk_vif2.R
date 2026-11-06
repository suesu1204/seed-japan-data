suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
INC <- "log_income_pc_adj"
vif <- function(dat, xs, fe) { W <- sapply(xs, function(v) resid(feols(as.formula(paste(v, "~ 1 |", fe)), dat)))
  out <- sapply(seq_along(xs), function(j) 1 / (1 - summary(lm(W[, j] ~ W[, -j]))$r.squared)); names(out) <- xs; round(out, 2) }
for (dep in c("log_p_condo", "log_p_house")) {
  d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = c(dep, "log_pop", "child_rate", "youth_rate", "elderly_rate", INC)][year >= 2015 & !is.na(get(dep)) & !is.na(get(INC))]
  cat(dep, "식 (2) 이동차분 VIF:", paste(names(v <- vif(d5, c("log_pop", "elderly_rate", INC), "year")), v, collapse = " | "), "\n")
  # 기준집단을 바꾸면 식 (3) 비율 변수 VIF가 어떻게 변하는지 (수준, 참고)
  d <- p[!is.na(get(dep)) & !is.na(get(INC))]
  for (ref in c("middle_rate", "child_rate")) { xs <- c("log_pop", setdiff(c("child_rate", "youth_rate", "middle_rate", "elderly_rate"), ref), INC)
    cat("  식 (3) 수준, 기준=", ref, ": ", paste(names(v <- vif(d, xs, "muni_code + year")), v, collapse = " | "), "\n", sep = "") } }
