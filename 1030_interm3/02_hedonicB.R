# 헤도닉 사양 B (Saita 속성: 면적·건폐율·용적률) + 추가: 사양 A를 1,000엔 규칙 없이.
# 입력: torihiki_hedB.csv, ../1030_interm2/panel_v2.csv (뼈대)
# 출력: hedonicB_coefs.csv, hedonicB_index.csv (log_p_land_hedB, n_land_hedB, log_p_condo_hedB, n_condo_hedB, log_p_land_hedA_nofloor, n_land_hedA_nofloor)
# 규칙: 토지만 1,000엔 미만 제외(B), 9999 → 역산 면적 + big_lot, 건폐율·용적률 숫자(Saita 방식) + 빈칸은 표본 평균 + ratio_na 더미, θ 5건 미만 결측
suppressPackageStartupMessages({ library(data.table); library(fixest) })
t <- fread("torihiki_hedB.csv", colClasses = list(character = c("muni_code", "building_year", "city_planning", "breadth")), na.strings = "")
stopifnot(nrow(t) == 2495150)
t[, muni_year := paste(muni_code, year, sep = "_")]
t[, ratio_na := as.integer(is.na(coverage_ratio) | is.na(floor_area_ratio))]
t[, cov := fifelse(ratio_na == 1, NA_real_, as.numeric(coverage_ratio))][, far := fifelse(ratio_na == 1, NA_real_, as.numeric(floor_area_ratio))]
t[, cov := fifelse(is.na(cov), mean(cov, na.rm = TRUE), cov), by = type][, far := fifelse(is.na(far), mean(far, na.rm = TRUE), far), by = type]
log <- c(); say <- function(...) { s <- paste0(...); cat(s, "\n"); log <<- c(log, s) }
idx_of <- function(m, dat, name) { f <- fixef(m)$muni_year; n <- dat[obs(m), .N, by = muni_year]
  x <- data.table(muni_year = names(f), v = as.numeric(f))[n, on = "muni_year"]; setnames(x, c("v", "N"), c(name, paste0("n_", sub("log_p_", "", name)))); x }
ct <- function(m, lab) { x <- as.data.table(coeftable(m), keep.rownames = "term"); setnames(x, c("term", "coef", "se", "t", "p")); x[, model := lab]; x[, .(model, term, coef, se, p)] }

# ---- 토지만 공통 변수 ----
L0 <- t[type == "宅地(土地)"]
L0[, big_lot := as.integer(area_sqm == 9999)][, area_use := fifelse(big_lot == 1, trade_price / unit_price, as.numeric(area_sqm))]
L0[, ln_p := log(unit_price)][, ln_area := log(area_use)]
L0[, city := fifelse(is.na(city_planning) | city_planning == "", "불명", city_planning)][, city := relevel(factor(city), ref = "第１種住居地域")]
b <- as.numeric(L0$breadth)
L0[, road := factor(fifelse(is.na(b), "불명", fifelse(b < 8, "8m미만", fifelse(b < 12, "8~12m미만", fifelse(b < 25, "12~25m미만", "25m이상")))), levels = c("8m미만", "8~12m미만", "12~25m미만", "25m이상", "불명"))]
# ---- B: 토지만 (1,000엔 미만 제외) ----
L <- L0[unit_price >= 1000]; say("B 토지만: ", nrow(L), "건 (1,000엔 미만 ", nrow(L0) - nrow(L), " 제외), 건폐율·용적률 빈칸 ", sum(L$ratio_na))
mLB <- feols(ln_p ~ ln_area + big_lot + cov + far + ratio_na | muni_year, data = L); say("  회귀 ", nobs(mLB), "건, within R2 ", round(r2(mLB, "wr2"), 3))
# ---- A(1,000엔 규칙 없음): 토지만 전체 ----
mLA0 <- feols(ln_p ~ ln_area + big_lot + city + road | muni_year, data = L0); say("A(하한 없음) 토지만: 회귀 ", nobs(mLA0), "건, within R2 ", round(r2(mLA0, "wr2"), 3))
# ---- B: 아파트 ----
C <- t[type == "中古マンション等" & area_sqm != 9999]
C[, ln_p := log(trade_price / area_sqm)][, ln_area := log(as.numeric(area_sqm))]
by <- C$building_year; by[!is.na(by) & by == "戦前"] <- "1945年"; byn <- suppressWarnings(as.integer(sub("年$", "", by)))
C[, age_na := as.integer(is.na(byn))]; age <- C$year - byn; age[!is.na(age) & age < 0] <- 0; age[is.na(age)] <- mean(age, na.rm = TRUE); C[, age := age]
say("B 아파트: ", nrow(C), "건, 건폐율·용적률 빈칸 ", sum(C$ratio_na))
mCB <- feols(ln_p ~ ln_area + age + age_na + cov + far + ratio_na | muni_year, data = C); say("  회귀 ", nobs(mCB), "건, within R2 ", round(r2(mCB, "wr2"), 3))
# ---- 출력 ----
coefs <- rbind(ct(mLB, "land_B"), ct(mLA0, "land_A_nofloor"), ct(mCB, "condo_B")); fwrite(coefs, "hedonicB_coefs.csv", bom = TRUE)
p <- fread("../1030_interm2/panel_v2.csv", colClasses = list(character = c("muni_code", "pref_code")))[, .(muni_code, year)][, muni_year := paste(muni_code, year, sep = "_")]
idx <- Reduce(function(a, b) merge(a, b, by = "muni_year", all.x = TRUE), list(p, idx_of(mLB, L, "log_p_land_hedB"), idx_of(mCB, C, "log_p_condo_hedB"), idx_of(mLA0, L0, "log_p_land_hedA_nofloor")))
for (k in c("land_hedB", "condo_hedB", "land_hedA_nofloor")) { nn <- paste0("n_", k); vv <- paste0("log_p_", k); idx[is.na(get(nn)), (nn) := 0L]; idx[get(nn) < 5, (vv) := NA_real_] }
idx <- idx[, .(muni_code, year, log_p_land_hedB, n_land_hedB, log_p_condo_hedB, n_condo_hedB, log_p_land_hedA_nofloor, n_land_hedA_nofloor)][order(muni_code, year)]
stopifnot(nrow(idx) == 27856); fwrite(idx, "hedonicB_index.csv", bom = TRUE)
say("지수 결측: 토지만 B ", round(mean(is.na(idx$log_p_land_hedB)), 3), " / 아파트 B ", round(mean(is.na(idx$log_p_condo_hedB)), 3), " / 토지만 A(하한 없음) ", round(mean(is.na(idx$log_p_land_hedA_nofloor)), 3))
print(coefs[!grepl("^city|^road", term), .(model, term, coef = round(coef, 4), se = round(se, 4))])
writeLines(log, "hedonicB_log.txt")
