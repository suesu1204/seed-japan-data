# 1101_nonlinear. 고령 비중 비선형 확인 3종. 소득 없음, 2010~2025. 고정효과 2종: year = 지역+연도(차분 구간) / prefyear = 지역+현×연도(차분 현×구간). 시정촌 군집.
# 기본식 H1 "둘 다": log P = 고령 + log_pop. 종속변수 4: 중앙값 토지·아파트, 헤도닉A(하한 없음) 토지·아파트
# A 제곱항 (수준): 고령 + 고령² → 한계효과 at 25/32/40%
# B 구간별 기울기 (수준): 꺾은선, 매듭 28·35% (전체 표본 3분위) → 구간 기울기 3개, 동일성 Wald
# C 출발 수준 × 변화 (5년 차분): Δ고령 + Δ고령×고령2010 → 2010년 고령 20/30/40%에서의 효과
# 입력 ../1031_interm/panel_v4.csv  출력 coefs_nonlinear.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1031_interm/panel_v4.csv", colClasses = list(character = c("muni_code", "pref_code")))
DEPS <- c(land = "log_p_land", condo = "log_p_condo", land_hedA = "log_p_land_hedA_nofloor", condo_hedA = "log_p_condo_hed")
K1 <- 28; K2 <- 35
p[, `:=`(eld2 = elderly_rate^2, s2 = pmax(elderly_rate - K1, 0), s3 = pmax(elderly_rate - K2, 0))]
p[, eld2010 := elderly_rate[year == 2010], by = muni_code]
ends <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1)), pref_code = pref_code[-1], eld2010 = eld2010[-1]),
               lapply(.SD, diff)), by = muni_code, .SDcols = c(DEPS, "log_pop", "elderly_rate")]
ld[, dxe := elderly_rate * eld2010]

rows <- list()
FE <- list(level = c(year = "muni_code + year", prefyear = "muni_code + pref_code^year"), ld5 = c(year = "period", prefyear = "pref_code^period"))
add <- function(design, version, dep, term, est, se, n) rows[[length(rows) + 1]] <<- data.table(design = design, version = version, fe = fe, dep = dep, term = term, coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = n)
combo <- function(m, cv) { b <- coef(m); V <- vcov(m); v <- setNames(rep(0, length(b)), names(b)); v[names(cv)] <- cv; c(sum(v * b), sqrt(as.numeric(t(v) %*% V %*% v))) }
for (fe in c("year", "prefyear")) for (d in names(DEPS)) { y <- DEPS[[d]]
  # A
  m <- feols(as.formula(paste(y, "~ elderly_rate + eld2 + log_pop |", FE$level[[fe]])), p, cluster = ~muni_code); ct <- coeftable(m); n <- nobs(m)
  for (t in rownames(ct)) add("A_quad", "level", d, t, ct[t, 1], ct[t, 2], n)
  for (e in c(25, 32, 40)) { r <- combo(m, c(elderly_rate = 1, eld2 = 2 * e)); add("A_quad", "level", d, paste0("me_at_", e), r[1], r[2], n) }
  # B
  m <- feols(as.formula(paste(y, "~ elderly_rate + s2 + s3 + log_pop |", FE$level[[fe]])), p, cluster = ~muni_code); ct <- coeftable(m); n <- nobs(m)
  for (t in rownames(ct)) add("B_spline", "level", d, t, ct[t, 1], ct[t, 2], n)
  add("B_spline", "level", d, "slope_lt28", ct["elderly_rate", 1], ct["elderly_rate", 2], n)
  r <- combo(m, c(elderly_rate = 1, s2 = 1)); add("B_spline", "level", d, "slope_28_35", r[1], r[2], n)
  r <- combo(m, c(elderly_rate = 1, s2 = 1, s3 = 1)); add("B_spline", "level", d, "slope_ge35", r[1], r[2], n)
  w <- wald(m, "^s2$|^s3$", print = FALSE); add("B_spline", "level", d, "wald_equal_slopes_p", w$p, NA_real_, n)
  # C
  m <- feols(as.formula(paste(y, "~ elderly_rate + dxe + log_pop |", FE$ld5[[fe]])), ld, cluster = ~muni_code); ct <- coeftable(m); n <- nobs(m)
  for (t in rownames(ct)) add("C_start_x_change", "ld5", d, t, ct[t, 1], ct[t, 2], n)
  for (e in c(20, 30, 40)) { r <- combo(m, c(elderly_rate = 1, dxe = e)); add("C_start_x_change", "ld5", d, paste0("eff_at_start_", e), r[1], r[2], n) }
}
out <- rbindlist(rows); fwrite(out, "coefs_nonlinear.csv", bom = TRUE); cat("coefs_nonlinear.csv", nrow(out), "행\n")
print(out[grepl("^me_at|^slope|^eff_at|wald", term), .(design, fe, dep, term, coef = round(coef, 4), se = round(se_cluster, 4), p = round(p, 3))], nrows = 100)
