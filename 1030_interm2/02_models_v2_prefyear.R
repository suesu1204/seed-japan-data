# v2 4번. 현×연도FE 재추정 (1030 1단계와 같은 식). 입력 panel_v2.csv, 비교 대상 coefs_v2_yearFE.csv
# 1017 02_models.R 과의 차이: (a) 고정효과 year → pref_code^year, period → pref_code^period
#                             (b) 종속변수 토지만·아파트 (토지+건물은 한국 자료에 대응 없음)
#                             (c) 표 이름 H1 / H2 / H2-1
# 입력: panel_v2.csv
# 출력: coefs_v2_prefyear.csv  (72행)
#       panel_filtered_v2.csv  (현×연도 회귀가 실제로 쓴 행. used_* 열 4개로 어느 회귀에 쓰였는지 표시)
#       compare_fe_v2.csv   (① v2 연도FE / ② 같은 표본에서 연도 FE / ③ 현×연도 FE)
# 실행: 1030_interm2/ 에서  Rscript 02_models_v2_prefyear.R
suppressPackageStartupMessages({ library(data.table); library(fixest) })

p <- fread("panel_v2.csv", colClasses = list(character = c("muni_code", "pref_code")))
stopifnot(nrow(p) == 27856)
DEPS  <- c(land = "log_p_land", condo = "log_p_condo")
RATES <- c("child_rate", "youth_rate", "middle_rate", "elderly_rate")

# ---- 5년 장기차분: 끝점 행 그대로 빼기 ----
ends <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
vars <- c(DEPS, "log_pop", RATES)
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]),
               lapply(.SD, diff)), by = muni_code, .SDcols = vars]
stopifnot(nrow(ld) == 1741 * 3)

specs <- list(
  list(tab = "H1",   model = "pop_only",   x = "log_pop"),
  list(tab = "H1",   model = "aging_only", x = "elderly_rate"),
  list(tab = "H1",   model = "both",       x = c("log_pop", "elderly_rate")),
  list(tab = "H2",   model = "ref_middle", x = c("log_pop", "child_rate", "youth_rate", "elderly_rate")),
  list(tab = "H2-1", model = "child",      x = c("log_pop", "child_rate")),
  list(tab = "H2-1", model = "youth",      x = c("log_pop", "youth_rate")),
  list(tab = "H2-1", model = "middle",     x = c("log_pop", "middle_rate")),
  list(tab = "H2-1", model = "elderly",    x = c("log_pop", "elderly_rate"))
)
unit_of <- function(term, version) {
  base <- if (term == "log_pop") "인구 1% 변화당 가격 % 변화" else
          if (term %in% c("child_plus_elderly", "child_minus_elderly")) "두 계수의 합/차 (비중 1%p당)" else
          "비중 1%p 변화당 log 가격 변화 (×100 = %)"
  if (version == "ld5") paste("5년간", base) else base
}
stars <- function(p) ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .1, "*", "")))

rows <- list()
collect <- function(m, tab, version, dep, model, fe, n_muni) {
  ct <- coeftable(m)
  out <- lapply(rownames(ct), function(term) data.table(table = tab, version = version, dep = dep, model = model, term = term,
    coef = ct[term, 1], se_cluster = ct[term, 2], nobs = nobs(m), n_muni = n_muni, fe = fe))
  if (tab == "H2") {
    b <- coef(m); V <- vcov(m)
    for (nm in c("child_plus_elderly", "child_minus_elderly")) {
      cvec <- setNames(rep(0, length(b)), names(b)); cvec["child_rate"] <- 1
      cvec["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
      out[[length(out) + 1]] <- data.table(table = tab, version = version, dep = dep, model = model, term = nm,
        coef = sum(cvec * b), se_cluster = sqrt(as.numeric(t(cvec) %*% V %*% cvec)), nobs = nobs(m), n_muni = n_muni, fe = fe)
    }
  }
  rbindlist(out)
}

# ---- ③ 현×연도 FE 추정 + 사용 행 기록 + ② 같은 표본에서 연도 FE ----
used <- list(level = data.table(row = seq_len(nrow(p))), ld5 = data.table(row = seq_len(nrow(ld))))
main <- list(); same <- list()
for (version in c("level", "ld5")) {
  dat <- if (version == "level") p else ld
  fe_new <- if (version == "level") "muni_code + pref_code^year" else "pref_code^period"
  fe_old <- if (version == "level") "muni_code + year" else "period"
  for (d in names(DEPS)) {
    used_rows <- NULL
    for (s in specs) {
      f_new <- as.formula(paste(DEPS[[d]], "~", paste(s$x, collapse = " + "), "|", fe_new))
      m <- feols(f_new, data = dat, cluster = ~muni_code)
      n_muni <- uniqueN(dat$muni_code[obs(m)])
      main[[length(main) + 1]] <- collect(m, s$tab, version, d, s$model, fe_new, n_muni)
      if (is.null(used_rows)) used_rows <- obs(m)   # 표본은 종속변수·버전별로 같음 (설명변수에 결측 없음)
      stopifnot(identical(sort(obs(m)), sort(used_rows)))
      # ② 같은 행으로 옛 고정효과
      f_old <- as.formula(paste(DEPS[[d]], "~", paste(s$x, collapse = " + "), "|", fe_old))
      m2 <- feols(f_old, data = dat[used_rows], cluster = ~muni_code)
      same[[length(same) + 1]] <- collect(m2, s$tab, version, d, s$model, fe_old, uniqueN(dat$muni_code[used_rows][obs(m2)]))
    }
    used[[version]][, paste0("used_", d) := row %in% used_rows]
  }
}
out <- rbindlist(main)
out[, `:=`(p = 2 * pnorm(-abs(coef / se_cluster)))][, `:=`(stars = stars(p), unit = mapply(unit_of, term, version))]
setcolorder(out, c("table", "version", "dep", "model", "term", "unit", "coef", "se_cluster", "p", "stars", "nobs", "n_muni", "fe"))
stopifnot(nrow(out) == 72)
fwrite(out, "coefs_v2_prefyear.csv", bom = TRUE)

# ---- panel_filtered.csv: 수준 회귀가 쓴 행 (used_level_*), 장기차분이 쓴 시정촌·구간 (used_ld5_*) ----
pf <- copy(p)
pf[, used_level_land := used$level$used_land][, used_level_condo := used$level$used_condo]
ldf <- copy(ld)[, used_ld5_land := used$ld5$used_land][, used_ld5_condo := used$ld5$used_condo]
# 장기차분 사용 여부는 구간 끝 연도 행에 표시 (2015/2020/2025)
ldf[, year := as.integer(substr(period, 6, 9))]
pf <- merge(pf, ldf[, .(muni_code, year, used_ld5_land, used_ld5_condo)], by = c("muni_code", "year"), all.x = TRUE)
pf[is.na(used_ld5_land), `:=`(used_ld5_land = FALSE, used_ld5_condo = FALSE)]
pf <- pf[used_level_land | used_level_condo | used_ld5_land | used_ld5_condo]
fwrite(pf, "panel_filtered_v2.csv", bom = TRUE)

# ---- compare_fe.csv ----
old <- fread("coefs_v2_yearFE.csv")
key <- c("table", "version", "dep", "model", "term")
same_dt <- rbindlist(same)[, p := 2 * pnorm(-abs(coef / se_cluster))]
pick <- function(dt, sfx) { x <- dt[, c(key, "coef", "se_cluster", "p", "nobs"), with = FALSE]
  setnames(x, c("coef", "se_cluster", "p", "nobs"), paste0(c("coef_", "se_", "p_", "nobs_"), sfx)); x }
cmp <- merge(pick(out, "prefyear"), pick(same_dt, "sameSample_year"), by = key, all.x = TRUE)
cmp <- merge(cmp, pick(old, "1017_year"), by = key, all.x = TRUE)
# 열 순서: 연도FE(1017) → 현×연도FE(변경 표본) → 연도FE(변경 표본)
setnames(cmp, c("coef_1017_year","se_1017_year","p_1017_year","nobs_1017_year", "coef_prefyear","se_prefyear","p_prefyear","nobs_prefyear",
                "coef_sameSample_year","se_sameSample_year","p_sameSample_year","nobs_sameSample_year"),
              c("coef_yearFE","se_yearFE","p_yearFE","nobs_yearFE", "coef_prefyearFE_sample","se_prefyearFE_sample","p_prefyearFE_sample","nobs_prefyearFE_sample",
                "coef_yearFE_sample","se_yearFE_sample","p_yearFE_sample","nobs_yearFE_sample"))
setcolorder(cmp, c(key, "coef_yearFE","se_yearFE","p_yearFE","nobs_yearFE",
                   "coef_prefyearFE_sample","se_prefyearFE_sample","p_prefyearFE_sample","nobs_prefyearFE_sample",
                   "coef_yearFE_sample","se_yearFE_sample","p_yearFE_sample","nobs_yearFE_sample"))
fwrite(cmp, "compare_fe_v2.csv", bom = TRUE)

cat("coefs_v2_prefyear.csv", nrow(out), "행 | panel_filtered_v2.csv", nrow(pf), "행 | compare_fe_v2 짝 없는 행:", sum(is.na(cmp$coef_yearFE)), "\n")
cat("사용 행 수 (수준):", sum(used$level$used_land), "토지만 /", sum(used$level$used_condo), "아파트 ; (장기차분):", sum(used$ld5$used_land), "/", sum(used$ld5$used_condo), "\n")
print(cmp[model %in% c("both", "ref_middle"), .(version, dep, term, yearFE = round(coef_yearFE, 4), prefyearFE = round(coef_prefyearFE_sample, 4), yearFE_s = round(coef_yearFE_sample, 4))], nrows = 100)
