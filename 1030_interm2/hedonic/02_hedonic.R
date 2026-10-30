# 헤도닉 2~3번. 변수 만들기 + 헤도닉 회귀 (계획서 2·3번 그대로)
# 입력: torihiki_hed.csv, ../panel_v2.csv (시정촌×연도 뼈대)
# 출력: hedonic_coefs.csv (속성 계수), hedonic_index.csv (muni_code, year, log_p_land_hed, n_land_hed, log_p_condo_hed, n_condo_hed)
# 지수 θ = 시정촌×연도 고정효과 추정치. 회귀에 들어간 거래 5건 미만이면 결측.
suppressPackageStartupMessages({ library(data.table); library(fixest) })
t <- fread("torihiki_hed.csv", colClasses = list(character = c("muni_code", "building_year", "city_planning", "breadth")), na.strings = "")
stopifnot(nrow(t) == 2495150)
t[, muni_year := paste(muni_code, year, sep = "_")]
t[, city := fifelse(is.na(city_planning) | city_planning == "", "불명", city_planning)]
log <- c()
say <- function(...) { s <- paste0(...); cat(s, "\n"); log <<- c(log, s) }

# ---------- 토지만 ----------
L <- t[type == "宅地(土地)"]
n0 <- nrow(L); L <- L[unit_price >= 1000]; say("토지만: 전체 ", n0, " → 1,000엔 미만 제외 후 ", nrow(L), " (제외 ", n0 - nrow(L), ")")
L[, big_lot := as.integer(area_sqm == 9999)]
L[, area_use := fifelse(big_lot == 1, trade_price / unit_price, as.numeric(area_sqm))]
say("  9999 행 ", sum(L$big_lot), "건, 역산 면적 중앙값 ", round(median(L[big_lot == 1, area_use])), "㎡, 최소 ", round(min(L[big_lot == 1, area_use])))
L[, ln_p := log(unit_price)][, ln_area := log(area_use)]
b <- as.numeric(L$breadth)
L[, road := fifelse(is.na(b), "불명", fifelse(b < 8, "8m미만", fifelse(b < 12, "8~12m미만", fifelse(b < 25, "12~25m미만", "25m이상"))))]
L[, road := factor(road, levels = c("8m미만", "8~12m미만", "12~25m미만", "25m이상", "불명"))]
L[, city := relevel(factor(city), ref = "第１種住居地域")]
mL <- feols(ln_p ~ ln_area + big_lot + city + road | muni_year, data = L)
say("  회귀 거래 수 ", nobs(mL), ", R2 within ", round(r2(mL, "wr2"), 3))
fL <- fixef(mL)$muni_year; nL <- L[obs(mL), .N, by = muni_year]
idxL <- data.table(muni_year = names(fL), log_p_land_hed = as.numeric(fL))[nL, on = "muni_year"]
setnames(idxL, "N", "n_land_hed")

# ---------- 아파트 ----------
C <- t[type == "中古マンション等"]
n0 <- nrow(C); C <- C[area_sqm != 9999]; say("아파트: 전체 ", n0, " → 면적 9999 제외 후 ", nrow(C), " (제외 ", n0 - nrow(C), ")")
C[, ln_p := log(trade_price / area_sqm)][, ln_area := log(as.numeric(area_sqm))]
by <- C$building_year; by[by == "戦前"] <- "1945年"; byn <- suppressWarnings(as.integer(sub("年$", "", by)))
C[, age_na := as.integer(is.na(byn))]
age <- C$year - byn; say("  건축연도 빈칸 ", sum(is.na(byn)), ", 戦前 ", sum(C$building_year == "戦前", na.rm = TRUE), ", 연령 음수→0 ", sum(age < 0, na.rm = TRUE))
age[!is.na(age) & age < 0] <- 0
age_mean <- mean(age, na.rm = TRUE); age[is.na(age)] <- age_mean; C[, age := age]
say("  연령 빈칸 대체값(표본 평균) ", round(age_mean, 2))
mC <- feols(ln_p ~ ln_area + age + age_na | muni_year, data = C)
say("  회귀 거래 수 ", nobs(mC), ", R2 within ", round(r2(mC, "wr2"), 3))
fC <- fixef(mC)$muni_year; nC <- C[obs(mC), .N, by = muni_year]
idxC <- data.table(muni_year = names(fC), log_p_condo_hed = as.numeric(fC))[nC, on = "muni_year"]
setnames(idxC, "N", "n_condo_hed")

# ---------- 계수표 ----------
ct <- function(m, lab) { x <- as.data.table(coeftable(m), keep.rownames = "term"); x[, model := lab]; setnames(x, c("term", "coef", "se", "t", "p", "model")); x }
coefs <- rbind(ct(mL, "land"), ct(mC, "condo"))[, .(model, term, coef, se, p)]
fwrite(coefs, "hedonic_coefs.csv", bom = TRUE)

# ---------- 지수표 (패널 뼈대 27,856행에 맞춤, 5건 미만 결측) ----------
p <- fread("../panel_v2.csv", colClasses = list(character = "muni_code"))[, .(muni_code, year)]
p[, muni_year := paste(muni_code, year, sep = "_")]
idx <- merge(merge(p, idxL, by = "muni_year", all.x = TRUE), idxC, by = "muni_year", all.x = TRUE)
idx[is.na(n_land_hed), n_land_hed := 0L][is.na(n_condo_hed), n_condo_hed := 0L]
idx[n_land_hed < 5, log_p_land_hed := NA_real_][n_condo_hed < 5, log_p_condo_hed := NA_real_]
idx <- idx[, .(muni_code, year, log_p_land_hed, n_land_hed, log_p_condo_hed, n_condo_hed)][order(muni_code, year)]
stopifnot(nrow(idx) == 27856)
fwrite(idx, "hedonic_index.csv", bom = TRUE)
say("지수 결측 비율: 토지만 ", round(mean(is.na(idx$log_p_land_hed)), 3), " (v2 중앙값 0.182) / 아파트 ", round(mean(is.na(idx$log_p_condo_hed)), 3), " (v2 중앙값 0.800)")
print(coefs[term %in% c("ln_area", "big_lot", "age", "age_na") | grepl("^road", term), .(model, term, coef = round(coef, 4), se = round(se, 4))])
writeLines(log, "hedonic_log.txt")
