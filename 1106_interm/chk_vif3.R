suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
INC <- "log_income_pc_adj"; V <- c("log_p_condo", "log_p_house", "log_pop", "child_rate", "youth_rate", "elderly_rate", INC)
vif <- function(dat, xs, fe) { W <- sapply(xs, function(v) resid(feols(as.formula(paste(v, "~ 1 |", fe)), dat)))
  out <- sapply(seq_along(xs), function(j) 1 / (1 - summary(lm(W[, j] ~ W[, -j]))$r.squared)); names(out) <- xs; round(out, 2) }
e <- p[year %in% c(2010, 2015, 2020)]; ld <- e[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))), lapply(.SD, diff)), by = muni_code, .SDcols = V]
for (dep in c("log_p_condo", "log_p_house")) { d <- ld[!is.na(get(dep)) & !is.na(get(INC))]
  cat(dep, "비중첩 장기차분 n=", nrow(d), "\n  식 (2):", paste(names(v <- vif(d, c("log_pop", "elderly_rate", INC), "period")), v, collapse = " | "),
      "\n  식 (3):", paste(names(v <- vif(d, c("log_pop", "child_rate", "youth_rate", "elderly_rate", INC), "period")), v, collapse = " | "), "\n") }
