suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1105_interm/panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
INC <- "log_income_pc_adj"; DEPS <- c(condo = "log_p_condo", house = "log_p_house", resi = "log_p_resi"); X <- c("log_pop", "child_rate", "youth_rate", "elderly_rate")
V <- c(DEPS, X, INC)
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = V][year >= 2015]
ld <- function(yrs) { e <- p[year %in% yrs]; e[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))), lapply(.SD, diff)), by = muni_code, .SDcols = V] }
S <- list(A = list(lv = p, d = d5, ld = ld(c(2010, 2015, 2020, 2025)), inc = FALSE), B = list(lv = p[year <= 2024], d = d5[year <= 2024], ld = ld(c(2010, 2015, 2020)), inc = FALSE), C = list(lv = p[year <= 2024], d = d5[year <= 2024], ld = ld(c(2010, 2015, 2020)), inc = TRUE))
st <- function(pv) ifelse(pv < .01, "***", ifelse(pv < .05, "**", ifelse(pv < .1, "*", "")))
cat(sprintf("%-6s %-6s %-9s %-22s %-22s %-22s\n", "표본", "방법", "종속", "유소년 δc", "고령 δe", "합 δc+δe (크기 비교)"))
for (s in names(S)) for (ver in c("level", "ld5", "roll")) for (d in names(DEPS)) {
  dat <- switch(ver, level = S[[s]]$lv, ld5 = S[[s]]$ld, roll = S[[s]]$d); fe <- switch(ver, level = "muni_code + year", ld5 = "period", roll = "year")
  m <- feols(as.formula(paste(DEPS[[d]], "~", paste(c(X, if (S[[s]]$inc) INC), collapse = "+"), "|", fe)), dat, cluster = ~muni_code)
  b <- coef(m); Vc <- vcov(m); cv <- setNames(rep(0, length(b)), names(b)); cv[c("child_rate", "elderly_rate")] <- 1
  est <- sum(cv * b); se <- sqrt(as.numeric(t(cv) %*% Vc %*% cv)); pv <- 2 * pnorm(-abs(est / se)); ct <- coeftable(m)
  f <- function(v) sprintf("%7.4f (%.4f)%-3s", ct[v, 1], ct[v, 2], st(ct[v, 4]))
  cat(sprintf("%-6s %-6s %-9s %s %s %7.4f (%.4f)%s\n", s, ver, d, f("child_rate"), f("elderly_rate"), est, se, st(pv))) }
