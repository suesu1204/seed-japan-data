# 소득 통제 재추정. 1030 사양(시정촌 + 현×연도 / 현×구간), 시정촌 군집.
# 종속변수 7개: 토지만 중앙값 v2 / 헤도닉A / 헤도닉B / 헤도닉A 하한 없음, 아파트 중앙값 v2 / 헤도닉A / 헤도닉B
# 비교 3열: none = 소득 없음(같은 기간) / raw = log_income_pc_raw / adj = log_income_pc_adj
# 기간: 수준 2010~2024 (2025 소득 없음). 장기차분: 2010→15, 2015→20 두 구간 (2020→25 는 2025 소득 없음)
# 표: H1(3), H2 기준 4종(합·차), H2-1(4). 출력 coefs_income.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("panel_v4.csv", colClasses = list(character = c("muni_code", "pref_code")))[year <= 2024]
DEPS <- c(land = "log_p_land", land_hedA = "log_p_land_hed", land_hedB = "log_p_land_hedB", land_hedA_nofloor = "log_p_land_hedA_nofloor",
          condo = "log_p_condo", condo_hedA = "log_p_condo_hed", condo_hedB = "log_p_condo_hedB")
RATES <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate")
INC <- c(none = NA, raw = "log_income_pc_raw", adj = "log_income_pc_adj")
ends <- p[year %in% c(2010, 2015, 2020)][order(muni_code, year)]
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]), lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", RATES, "log_income_pc_raw", "log_income_pc_adj")]
rows <- list(); add <- function(...) rows[[length(rows) + 1]] <<- data.table(...)
for (version in c("level", "ld5")) { dat <- if (version == "level") p else ld; fe <- if (version == "level") "muni_code + pref_code^year" else "pref_code^period"
  for (d in names(DEPS)) for (ic in names(INC)) {
    # 소득 없음도 소득 결측 행을 빼서 표본을 맞춤
    dd <- dat[!is.na(log_income_pc_raw)]
    run <- function(tab, model, ref, xs) { x <- if (is.na(INC[[ic]])) xs else c(xs, INC[[ic]])
      m <- feols(as.formula(paste(DEPS[[d]], "~", paste(x, collapse = " + "), "|", fe)), data = dd, cluster = ~muni_code); ct <- coeftable(m)
      for (term in rownames(ct)) add(table = tab, version = version, dep = d, income = ic, model = model, ref = ref, term = term, coef = ct[term, 1], se_cluster = ct[term, 2], p = ct[term, 4], nobs = nobs(m))
      if (tab == "H2") { b <- coef(m); V <- vcov(m); for (nm in c("child_plus_elderly", "child_minus_elderly")) { cv <- setNames(rep(0, length(b)), names(b))
        if ("child_rate" %in% names(b)) cv["child_rate"] <- 1; if ("elderly_rate" %in% names(b)) cv["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
        est <- sum(cv * b); se <- sqrt(as.numeric(t(cv) %*% V %*% cv)); add(table = tab, version = version, dep = d, income = ic, model = model, ref = ref, term = nm, coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = nobs(m)) } } }
    run("H1", "pop_only", "", "log_pop"); run("H1", "aging_only", "", "elderly_rate"); run("H1", "both", "", c("log_pop", "elderly_rate"))
    for (ref in c("middle", "child", "youth", "elderly")) run("H2", paste0("ref_", ref), ref, c("log_pop", unname(RATES[names(RATES) != ref])))
    for (m in names(RATES)) run("H2-1", m, "", c("log_pop", RATES[[m]]))
  } }
out <- rbindlist(rows); fwrite(out, "coefs_income.csv", bom = TRUE); cat("coefs_income.csv", nrow(out), "행\n")
print(out[table == "H1" & model == "both" & term %in% c("log_pop", "elderly_rate", "log_income_pc_raw", "log_income_pc_adj"), .(version, dep, income, term, coef = round(coef, 4), se = round(se_cluster, 4), p = round(p, 3), nobs)], nrows = 100)
