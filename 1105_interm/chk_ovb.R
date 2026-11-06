suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[!is.na(log_income_pc_adj)]
for (s in c("house", "condo", "land")) { d <- p[!is.na(get(paste0("log_p_", s)))]; dep <- paste0("log_p_", s)
  a <- coef(feols(as.formula(paste(dep, "~ elderly_rate + log_income_pc_adj | muni_code + year")), d))["elderly_rate"]
  b <- coef(feols(as.formula(paste(dep, "~ log_pop + elderly_rate + log_income_pc_adj | muni_code + year")), d))
  g <- coef(feols(log_pop ~ elderly_rate + log_income_pc_adj | muni_code + year, d))["elderly_rate"]
  cat(sprintf("%-5s 고령만 %7.4f = 직접 %7.4f + 인구계수 %5.3f × (고령 1%%p당 log인구 변화 %7.4f = %7.4f)\n", s, a, b["elderly_rate"], b["log_pop"], g, b["log_pop"] * g)) }
