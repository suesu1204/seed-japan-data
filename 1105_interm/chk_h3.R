suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
INC <- "log_income_pc_adj"; st <- function(pv) ifelse(pv < .01, "***", ifelse(pv < .05, "**", ifelse(pv < .1, "*", "")))
R <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate")
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = c("log_p_condo", "log_p_land", "log_p_house", "log_pop", R, INC)][year >= 2015]
for (inc in c("no", "yes")) for (dep in c("log_p_condo", "log_p_land")) for (ver in c("수준", "이동차분")) {
  dat <- if (ver == "수준") p else d5; if (inc == "yes") dat <- dat[!is.na(get(INC))]; fe <- if (ver == "수준") "muni_code + year" else "year"
  xs <- c("log_pop", if (inc == "yes") INC)
  cat(sprintf("\n[%s | 소득 %s | %s]\n", sub("log_p_", "", dep), inc, ver))
  for (ref in c("middle", "child")) { m <- feols(as.formula(paste(dep, "~", paste(c(xs, unname(R[names(R) != ref])), collapse = "+"), "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(m)
    cat(sprintf("  기준=%-7s", ref)); for (v in unname(R[names(R) != ref])) cat(sprintf("  %s %7.4f (%.4f)%-3s", sub("_rate", "", v), ct[v,1], ct[v,2], st(ct[v,4]))); cat(sprintf("  n=%d\n", nobs(m))) } }
