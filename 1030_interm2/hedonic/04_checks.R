# 헤도닉 확인 2종 (H1 '둘 다' 모형, 현×연도FE / 현×구간FE, 시정촌 군집)
#  A. 중앙값 종속변수를 헤도닉과 같은 표본(헤도닉 지수가 있는 시정촌·연도)으로 → 표본 차이 효과
#  B. 토지만 헤도닉에서 도로폭 변수 제외하고 θ 다시 추정 → '도로폭 불명' 더미 효과
# 출력: check_results.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../panel_v2.csv", colClasses = list(character = c("muni_code", "pref_code")))
mk_ld <- function(p, vars) { e <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
  e[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1]), lapply(.SD, diff)), by = muni_code, .SDcols = vars] }
fit <- function(dat, dep, fe, lab, dep_lab, version) {
  m <- feols(as.formula(paste(dep, "~ log_pop + elderly_rate |", fe)), dat, cluster = ~muni_code)
  ct <- coeftable(m)
  data.table(check = lab, version = version, dep = dep_lab, term = rownames(ct), coef = ct[, 1], se = ct[, 2], p = ct[, 4], nobs = nobs(m))
}
res <- list()
# ---- 기준: 중앙값(전체 표본) / 헤도닉 (이미 있음) ----
for (d in c("land", "condo")) {
  med <- paste0("log_p_", d); hed <- paste0("log_p_", d, "_hed")
  same <- p[!is.na(get(hed))]                                   # 헤도닉 지수 있는 행만
  res[[length(res)+1]] <- fit(p,    med, "muni_code + pref_code^year", "중앙값(전체 표본)", d, "level")
  res[[length(res)+1]] <- fit(same, med, "muni_code + pref_code^year", "A. 중앙값(헤도닉 표본)", d, "level")
  res[[length(res)+1]] <- fit(p,    hed, "muni_code + pref_code^year", "헤도닉", d, "level")
  ld_all <- mk_ld(p, c(med, hed, "log_pop", "elderly_rate"))
  ld_same <- ld_all[!is.na(get(hed))]
  res[[length(res)+1]] <- fit(ld_all,  med, "pref_code^period", "중앙값(전체 표본)", d, "ld5")
  res[[length(res)+1]] <- fit(ld_same, med, "pref_code^period", "A. 중앙값(헤도닉 표본)", d, "ld5")
  res[[length(res)+1]] <- fit(ld_all,  hed, "pref_code^period", "헤도닉", d, "ld5")
}
# ---- B. 토지만 헤도닉, 도로폭 제외 ----
t <- fread("torihiki_hed.csv", colClasses = list(character = c("muni_code", "building_year", "city_planning", "breadth")), na.strings = "")
L <- t[type == "宅地(土地)" & unit_price >= 1000]
L[, muni_year := paste(muni_code, year, sep = "_")][, big_lot := as.integer(area_sqm == 9999)]
L[, area_use := fifelse(big_lot == 1, trade_price / unit_price, as.numeric(area_sqm))][, ln_p := log(unit_price)][, ln_area := log(area_use)]
L[, city := fifelse(is.na(city_planning) | city_planning == "", "불명", city_planning)][, city := relevel(factor(city), ref = "第１種住居地域")]
mB <- feols(ln_p ~ ln_area + big_lot + city | muni_year, data = L)
fB <- fixef(mB)$muni_year; nB <- L[obs(mB), .N, by = muni_year]
idx <- data.table(muni_year = names(fB), hed_noroad = as.numeric(fB))[nB, on = "muni_year"][N < 5, hed_noroad := NA_real_]
p2 <- copy(p)[, muni_year := paste(muni_code, year, sep = "_")]
p2 <- merge(p2, idx[, .(muni_year, hed_noroad)], by = "muni_year", all.x = TRUE)
res[[length(res)+1]] <- fit(p2, "hed_noroad", "muni_code + pref_code^year", "B. 헤도닉(도로폭 제외)", "land", "level")
res[[length(res)+1]] <- fit(mk_ld(p2, c("hed_noroad", "log_pop", "elderly_rate")), "hed_noroad", "pref_code^period", "B. 헤도닉(도로폭 제외)", "land", "ld5")
out <- rbindlist(res); fwrite(out, "check_results.csv", bom = TRUE)
out[, cell := sprintf("%.4f (%.4f)%s", coef, se, ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .1, "*", ""))))]
print(dcast(out[term == "elderly_rate"], version + dep ~ check, value.var = "cell"))
print(dcast(out[term == "elderly_rate"], version + dep ~ check, value.var = "nobs"))
print(dcast(out[term == "log_pop"], version + dep ~ check, value.var = "cell"))
