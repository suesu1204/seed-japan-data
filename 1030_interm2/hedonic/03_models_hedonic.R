# 헤도닉 5번. 분석 회귀: 종속변수 = 헤도닉 지수. 1030 사양(시정촌 + 현×연도 / 현×구간), 시정촌 군집
# 입력: ../panel_v2.csv (33열)   출력: coefs_hedonic.csv (72행), compare_median_hedonic.csv (중앙값 v2 vs 헤도닉)
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../panel_v2.csv", colClasses = list(character = c("muni_code", "pref_code")))
stopifnot(nrow(p) == 27856, "log_p_land_hed" %in% names(p))
DEPS  <- c(land = "log_p_land_hed", condo = "log_p_condo_hed")
RATES <- c("child_rate", "youth_rate", "middle_rate", "elderly_rate")
ends <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]),
               lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", RATES)]
specs <- list(
  list(tab = "H1",   model = "pop_only",   x = "log_pop"),
  list(tab = "H1",   model = "aging_only", x = "elderly_rate"),
  list(tab = "H1",   model = "both",       x = c("log_pop", "elderly_rate")),
  list(tab = "H2",   model = "ref_middle", x = c("log_pop", "child_rate", "youth_rate", "elderly_rate")),
  list(tab = "H2-1", model = "child",      x = c("log_pop", "child_rate")),
  list(tab = "H2-1", model = "youth",      x = c("log_pop", "youth_rate")),
  list(tab = "H2-1", model = "middle",     x = c("log_pop", "middle_rate")),
  list(tab = "H2-1", model = "elderly",    x = c("log_pop", "elderly_rate")))
stars <- function(p) ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .1, "*", "")))
rows <- list()
for (version in c("level", "ld5")) {
  dat <- if (version == "level") p else ld
  fe  <- if (version == "level") "muni_code + pref_code^year" else "pref_code^period"
  for (d in names(DEPS)) for (s in specs) {
    m <- feols(as.formula(paste(DEPS[[d]], "~", paste(s$x, collapse = " + "), "|", fe)), data = dat, cluster = ~muni_code)
    ct <- coeftable(m); n_muni <- uniqueN(dat$muni_code[obs(m)])
    add <- function(term, est, se) rows[[length(rows) + 1]] <<- data.table(table = s$tab, version = version, dep = d, model = s$model, term = term,
      coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = nobs(m), n_muni = n_muni, fe = fe)
    for (term in rownames(ct)) add(term, ct[term, 1], ct[term, 2])
    if (s$tab == "H2") { b <- coef(m); V <- vcov(m)
      for (nm in c("child_plus_elderly", "child_minus_elderly")) {
        cvec <- setNames(rep(0, length(b)), names(b)); cvec["child_rate"] <- 1; cvec["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
        add(nm, sum(cvec * b), sqrt(as.numeric(t(cvec) %*% V %*% cvec))) } }
  }
}
out <- rbindlist(rows)[, stars := stars(p)]
stopifnot(nrow(out) == 72)
fwrite(out, "coefs_hedonic.csv", bom = TRUE)
key <- c("table", "version", "dep", "model", "term")
med <- fread("../coefs_v2_prefyear.csv")[, c(key, "coef", "se_cluster", "p", "nobs"), with = FALSE]
setnames(med, c("coef", "se_cluster", "p", "nobs"), c("coef_median", "se_median", "p_median", "nobs_median"))
hed <- out[, c(key, "coef", "se_cluster", "p", "nobs"), with = FALSE]; setnames(hed, c("coef", "se_cluster", "p", "nobs"), c("coef_hedonic", "se_hedonic", "p_hedonic", "nobs_hedonic"))
cmp <- merge(med, hed, by = key, all = TRUE); stopifnot(nrow(cmp) == 72, !anyNA(cmp$coef_median), !anyNA(cmp$coef_hedonic))
fwrite(cmp, "compare_median_hedonic.csv", bom = TRUE)
cat("coefs_hedonic.csv", nrow(out), "행 | compare 72행 짝 완전\n")
print(cmp[model %in% c("both", "ref_middle"), .(version, dep, term, median = round(coef_median, 4), hedonic = round(coef_hedonic, 4), p_med = round(p_median, 3), p_hed = round(p_hedonic, 3), n_med = nobs_median, n_hed = nobs_hedonic)], nrows = 100)
