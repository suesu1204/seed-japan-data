suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
INC <- "log_income_pc_adj"
vif <- function(dat, xs, fe) { W <- sapply(xs, function(v) resid(feols(as.formula(paste(v, "~ 1 |", fe)), dat))); R <- cor(W)
  out <- sapply(seq_along(xs), function(j) 1 / (1 - summary(lm(W[, j] ~ W[, -j]))$r.squared)); names(out) <- xs; list(vif = round(out, 2), cor = round(R, 2)) }
for (dep in c("log_p_condo", "log_p_house")) { d <- p[!is.na(get(dep)) & !is.na(get(INC))]; cat("\n=====", dep, "표본 (소득 통제, 2010~2024) =====\n")
  r2 <- vif(d, c("log_pop", "elderly_rate", INC), "muni_code + year"); cat("식 (2) within VIF:", paste(names(r2$vif), r2$vif, collapse = " | "), "\n")
  r3 <- vif(d, c("log_pop", "child_rate", "youth_rate", "elderly_rate", INC), "muni_code + year"); cat("식 (3) within VIF:", paste(names(r3$vif), r3$vif, collapse = " | "), "\n"); print(r3$cor)
  d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = c(dep, "log_pop", "child_rate", "youth_rate", "elderly_rate", INC)][year >= 2015 & !is.na(get(dep)) & !is.na(get(INC))]
  r5 <- vif(d5, c("log_pop", "child_rate", "youth_rate", "elderly_rate", INC), "year"); cat("식 (3) 이동차분 VIF:", paste(names(r5$vif), r5$vif, collapse = " | "), "\n") }
