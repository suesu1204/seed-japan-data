# 1030 3단계. H2 기준 범주 변경 (유소년 / 청년 / 고령 기준). 계획서 3단계.
# 고정효과 3종 비교: yearFE(1017 사양, 전체 표본) / prefyearFE_sample(현×연도, 1단계 사양) / yearFE_sample(현×연도가 쓴 표본에서 연도FE). 시정촌 군집, 종속변수 토지만·아파트
# 식: log 가격 = log_pop + (기준을 뺀 세 비중). 추가 행: 유소년+고령 합, 유소년−고령 차 (기준이 유소년/고령이면 그 계수는 0이므로 합·차는 남은 쪽 계수와 같음)
# 입력: ../1017_interm/panel.csv   출력: coefs_refcat.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })

p <- fread("../1017_interm/panel.csv", colClasses = list(character = c("muni_code", "pref_code")))
DEPS  <- c(land = "log_p_land", condo = "log_p_condo")
RATES <- c(child = "child_rate", youth = "youth_rate", middle = "middle_rate", elderly = "elderly_rate")
ends <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]),
               lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", RATES)]
stars <- function(p) ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .1, "*", "")))

rows <- list()
for (version in c("level", "ld5")) {
  dat <- if (version == "level") p else ld
  fe_new <- if (version == "level") "muni_code + pref_code^year" else "pref_code^period"
  fe_old <- if (version == "level") "muni_code + year" else "period"
  for (d in names(DEPS)) for (ref in c("middle", "child", "youth", "elderly")) {
    xs <- c("log_pop", unname(RATES[names(RATES) != ref]))
    f_new <- as.formula(paste(DEPS[[d]], "~", paste(xs, collapse = " + "), "|", fe_new))
    f_old <- as.formula(paste(DEPS[[d]], "~", paste(xs, collapse = " + "), "|", fe_old))
    m_new <- feols(f_new, data = dat, cluster = ~muni_code)
    used  <- obs(m_new)
    fits <- list(yearFE = feols(f_old, data = dat, cluster = ~muni_code),
                 prefyearFE_sample = m_new,
                 yearFE_sample = feols(f_old, data = dat[used], cluster = ~muni_code))
    for (spec in names(fits)) {
      m <- fits[[spec]]; ct <- coeftable(m); b <- coef(m); V <- vcov(m)
      dd <- if (spec == "yearFE_sample") dat[used] else dat
      n_muni <- uniqueN(dd$muni_code[obs(m)])
      add <- function(term, est, se) rows[[length(rows) + 1]] <<- data.table(table = "H2", version = version, dep = d, ref = ref, spec = spec, term = term,
        coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = nobs(m), n_muni = n_muni)
      for (term in rownames(ct)) add(term, ct[term, 1], ct[term, 2])
      cvec0 <- setNames(rep(0, length(b)), names(b))
      for (nm in c("child_plus_elderly", "child_minus_elderly")) {
        cvec <- cvec0
        if ("child_rate" %in% names(b)) cvec["child_rate"] <- 1
        if ("elderly_rate" %in% names(b)) cvec["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
        add(nm, sum(cvec * b), sqrt(as.numeric(t(cvec) %*% V %*% cvec)))
      }
    }
  }
}
out <- rbindlist(rows)[, stars := stars(p)]
out[, unit := fifelse(term == "log_pop", "인구 1% 변화당 가격 % 변화",
              fifelse(term %in% c("child_plus_elderly", "child_minus_elderly"), "두 계수의 합/차 (비중 1%p당)",
                      paste0("비중 1%p 변화당 log 가격 변화 (기준=", ref, ")")))]
out[version == "ld5", unit := paste("5년간", unit)]
setcolorder(out, c("table", "version", "dep", "ref", "spec", "term", "unit", "coef", "se_cluster", "p", "stars", "nobs", "n_muni"))
stopifnot(nrow(out) == 2 * 2 * 4 * 3 * 6)   # 버전2 × 종속2 × 기준4 × 사양3 × (계수4 + 합차2) = 288
fwrite(out, "coefs_refcat.csv", bom = TRUE)
cat("coefs_refcat.csv", nrow(out), "행\n")
