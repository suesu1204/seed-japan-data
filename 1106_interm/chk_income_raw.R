# 소득 발표값(log_income_pc_raw, 2024년도 납세의무자 수 미보정) vs 보간값(log_income_pc_adj) 비교. 표본 C(2010~2024 소득 통제)만, 07_models_final.R과 같은 사양.
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)][year <= 2024]
DEPS <- c(condo = "log_p_condo", house = "log_p_house", resi = "log_p_resi")
R <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate"); INCS <- c(adj = "log_income_pc_adj", raw = "log_income_pc_raw")
V <- c(DEPS, "log_pop", R, INCS)
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = V][year >= 2015]
e <- p[year %in% c(2010, 2015, 2020)]; ld <- e[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))), lapply(.SD, diff)), by = muni_code, .SDcols = V]
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (ver in c("level", "ld5", "roll")) { dat <- switch(ver, level = p, ld5 = ld, roll = d5); fe <- switch(ver, level = "muni_code + year", ld5 = "period", roll = "year")
  for (d in names(DEPS)) for (inc in names(INCS)) {
    run <- function(model, xs) { m <- feols(as.formula(paste(DEPS[[d]], "~", paste(c(xs, INCS[[inc]]), collapse = " + "), "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(m)
      for (t in rownames(ct)) add(version = ver, dep = d, income = inc, model = model, term = t, coef = ct[t, 1], se = ct[t, 2], p = ct[t, 4], nobs = nobs(m)) }
    run("pop_only", "log_pop"); run("aging_only", "elderly_rate"); run("both", c("log_pop", "elderly_rate"))
    run("ref_middle", c("log_pop", unname(R[c("child", "youth", "elderly")]))); run("ref_child", c("log_pop", unname(R[c("youth", "middle", "elderly")])))
  } }
out <- rbindlist(rows); fwrite(out, "coefs_income_raw.csv", bom = TRUE)
st <- function(p) fifelse(p < .01, "***", fifelse(p < .05, "**", fifelse(p < .1, "*", "")))
out[, cell := sprintf("%.4f%s (%.4f)", coef, st(p), se)]
w <- dcast(out[term %in% c("log_pop", "elderly_rate", "log_income_pc_adj", "log_income_pc_raw")], dep + model + version + term ~ income, value.var = "cell")
s <- dcast(out[term %in% c("log_pop", "elderly_rate")], dep + model + version + term ~ income, value.var = "p")
s[, star_change := st(adj) != st(raw)]
cat("별표 바뀐 칸:", sum(s$star_change), "/", nrow(s), "\n"); print(s[star_change == TRUE])
cat("\n== 아파트 고령화율 계수 (both, H2) ==\n"); print(w[dep == "condo" & model == "both" & term == "elderly_rate"])
cat("\n== 아파트 소득 계수 (both) ==\n"); print(w[dep == "condo" & model == "both" & term %like% "income"])
cat("\n== 전체 ==\n"); print(w[order(dep, model, version)], nrows = 500)
