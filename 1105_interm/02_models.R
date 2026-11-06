# 1105_interm 3단계: 거주용 단독주택(log_p_house) · 아파트(log_p_condo) 회귀.
# 종속변수: 단독주택(연면적당)·아파트·단독주택+아파트 합산(log_p_resi). 모형: H1 인구만·고령화만·둘 다, H3 4연령 비중(중장년 기준). 수준/5년 차분 × 지역+연도 FE × 소득 통제 유무.
# 소득 있음 = 2010~2024 (차분 2010→15, 15→20), 소득 없음 = 2010~2025 (차분 3구간). 표준오차 시정촌 군집.
# 입력 panel_v5.csv  출력 coefs.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p0 <- fread("panel_v5.csv", colClasses = list(character = c("muni_code", "pref_code")))
DEPS <- c(house = "log_p_house", condo = "log_p_condo", resi = "log_p_resi")
RATES <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate"); INC <- "log_income_pc_adj"
FE <- list(level = c(year = "muni_code + year", prefyear = "muni_code + pref_code^year"), ld5 = c(year = "period", prefyear = "pref_code^period"))
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (inc in c("no", "yes")) {
  p <- if (inc == "yes") p0[!is.na(get(INC))] else p0
  yrs <- if (inc == "yes") c(2010, 2015, 2020) else c(2010, 2015, 2020, 2025)
  ends <- p[year %in% yrs][order(muni_code, year)]
  ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]), lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", RATES, INC)]
  for (version in c("level", "ld5")) { dat <- if (version == "level") p else ld
    for (fe in c("year")) for (d in names(DEPS)) {
      run <- function(tab, model, xs) {
        xs2 <- if (inc == "yes") c(xs, INC) else xs
        m <- feols(as.formula(paste(DEPS[[d]], "~", paste(xs2, collapse = " + "), "|", FE[[version]][[fe]])), dat, cluster = ~muni_code); ct <- coeftable(m)
        for (t in rownames(ct)) add(income = inc, table = tab, version = version, fe = fe, dep = d, model = model, term = t, coef = ct[t, 1], se_cluster = ct[t, 2], p = ct[t, 4], nobs = nobs(m)) }
      run("H1", "pop_only", "log_pop"); run("H1", "aging_only", "elderly_rate"); run("H1", "both", c("log_pop", "elderly_rate"))
      run("H3", "ref_middle", c("log_pop", unname(RATES[names(RATES) != "middle"])))
    } } }
out <- rbindlist(rows); fwrite(out, "coefs.csv", bom = TRUE); cat("coefs.csv", nrow(out), "행\n")
print(out[table == "H1" & model == "both" & term == "elderly_rate", .(income, version, fe, dep, coef = round(coef, 4), se = round(se_cluster, 4), nobs)])
