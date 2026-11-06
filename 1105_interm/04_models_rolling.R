# 1105_interm 5단계: 5년 이동차분. 구간 = t−5 → t, t = 2015..2025 (소득 있음: 2015..2024, 10구간). 종료연도 고정효과, 시정촌 군집 SE.
# 종속변수 단독주택·아파트·단독주택+아파트·토지. 모형: H1 인구만·고령화만·둘 다, H3 4연령(중장년 기준). 소득 통제 유무.
# 입력 panel_v5.csv  출력 coefs_rolling.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))[order(muni_code, year)]
DEPS <- c(house = "log_p_house", condo = "log_p_condo", resi = "log_p_resi", land = "log_p_land")
RATES <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate"); INC <- "log_income_pc_adj"
V <- c(DEPS, "log_pop", RATES, INC)
d5 <- p[, c(.(year = year), lapply(.SD, function(x) x - shift(x, 5))), by = muni_code, .SDcols = V][year >= 2015]
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (inc in c("no", "yes")) { dat <- if (inc == "yes") d5[!is.na(get(INC))] else d5
  stopifnot(inc == "no" || max(dat$year) == 2024)
  for (d in names(DEPS)) {
    run <- function(tab, model, xs) { xs2 <- if (inc == "yes") c(xs, INC) else xs
      m <- feols(as.formula(paste(DEPS[[d]], "~", paste(xs2, collapse = " + "), "| year")), dat, cluster = ~muni_code); ct <- coeftable(m)
      for (t in rownames(ct)) add(income = inc, table = tab, dep = d, model = model, term = t, coef = ct[t, 1], se_cluster = ct[t, 2], p = ct[t, 4], nobs = nobs(m), n_muni = length(unique(dat[!is.na(get(DEPS[[d]])), muni_code]))) }
    run("H1", "pop_only", "log_pop"); run("H1", "aging_only", "elderly_rate"); run("H1", "both", c("log_pop", "elderly_rate"))
    run("H3", "ref_middle", c("log_pop", unname(RATES[names(RATES) != "middle"]))) } }
out <- rbindlist(rows); fwrite(out, "coefs_rolling.csv", bom = TRUE); cat("coefs_rolling.csv", nrow(out), "행\n")
print(out[table == "H1" & model == "both" & term == "elderly_rate", .(income, dep, coef = round(coef, 4), se = round(se_cluster, 4), p = round(p, 3), nobs)])
