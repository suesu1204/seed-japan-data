# v2 3번. 연도FE 재추정 (1017 2단계와 같은 식). 입력 panel_v2.csv, 종속변수 토지만·아파트, 표 이름 H1/H2/H2-1
# 입력: panel_v2.csv
# 출력: coefs_v2_yearFE.csv  (표 A / A-2 / H1-1 × 종속변수 3종 × 수준·5년 장기차분, 시정촌 군집 표준오차, 단위 열 포함)
#        Wald(δ_child + δ_elderly = 0) 와 차이(δ_child − δ_elderly) 는 term 행으로 같은 파일에 기록
suppressPackageStartupMessages({ library(data.table); library(fixest) })
# 1030_interm2/ 에서 실행: Rscript 01_models_v2_yearFE.R

p <- fread("panel_v2.csv", colClasses = list(character = c("muni_code", "pref_code")))
stopifnot(nrow(p) == 27856)
DEPS  <- c(land = "log_p_land", condo = "log_p_condo")
RATES <- c("child_rate", "youth_rate", "middle_rate", "elderly_rate")

# ---- 5년 장기차분: 끝점 행 그대로 빼기 (2010→15, 15→20, 20→25) ----
ends <- p[year %in% c(2010, 2015, 2020, 2025)][order(muni_code, year)]
vars <- c(DEPS, "log_pop", RATES)
ld <- ends[, c(list(period = paste0(head(year, -1), "_", tail(year, -1))),
               lapply(.SD, function(x) diff(x))), by = muni_code, .SDcols = vars]
stopifnot(nrow(ld) == 1741 * 3)

# ---- 모형 목록 ----
specs <- list(
  list(tab = "H1",  model = "pop_only",   x = "log_pop"),
  list(tab = "H1",  model = "aging_only", x = "elderly_rate"),
  list(tab = "H1",  model = "both",       x = c("log_pop", "elderly_rate")),
  list(tab = "H2-1", model = "child",      x = c("log_pop", "child_rate")),
  list(tab = "H2-1", model = "youth",      x = c("log_pop", "youth_rate")),
  list(tab = "H2-1", model = "middle",     x = c("log_pop", "middle_rate")),
  list(tab = "H2-1", model = "elderly",    x = c("log_pop", "elderly_rate")),
  list(tab = "H2",  model = "ref_middle", x = c("log_pop", "child_rate", "youth_rate", "elderly_rate"))
)
unit_of <- function(term, version) {
  base <- if (term == "log_pop") "인구 1% 변화당 가격 % 변화" else "비중 1%p 변화당 log 가격 변화 (×100 = %)"
  if (version == "ld5") paste("5년간", base) else base
}
stars <- function(p) ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .1, "*", "")))

rows <- list()
add <- function(tab, version, dep, model, term, coef, se, nobs, n_muni) {
  t <- coef / se; pv <- 2 * pnorm(-abs(t))
  rows[[length(rows) + 1]] <<- data.table(table = tab, version = version, dep = dep, model = model, term = term,
    unit = unit_of(term, version), coef = coef, se_cluster = se, p = pv, stars = stars(pv), nobs = nobs, n_muni = n_muni)
}

for (version in c("level", "ld5")) {
  dat <- if (version == "level") p else ld
  fe  <- if (version == "level") "muni_code + year" else "period"
  for (d in names(DEPS)) for (s in specs) {
    f <- as.formula(paste(DEPS[[d]], "~", paste(s$x, collapse = " + "), "|", fe))
    m <- feols(f, data = dat, cluster = ~muni_code)
    ct <- coeftable(m); n_muni <- uniqueN(dat$muni_code[obs(m)])
    for (term in rownames(ct)) add(s$tab, version, d, s$model, term, ct[term, 1], ct[term, 2], nobs(m), n_muni)
    if (s$tab == "H2") {   # Wald: δ_child + δ_elderly = 0 ; 보조: δ_child − δ_elderly
      b <- coef(m); V <- vcov(m)
      for (nm in c("child_plus_elderly", "child_minus_elderly")) {
        cvec <- setNames(rep(0, length(b)), names(b)); cvec["child_rate"] <- 1
        cvec["elderly_rate"] <- if (nm == "child_plus_elderly") 1 else -1
        est <- sum(cvec * b); se <- sqrt(as.numeric(t(cvec) %*% V %*% cvec))
        add(s$tab, version, d, s$model, nm, est, se, nobs(m), n_muni)
      }
    }
  }
}
out <- rbindlist(rows)
out[term %in% c("child_plus_elderly", "child_minus_elderly"), unit := "두 계수의 합/차 (비중 1%p당)"]
stopifnot(nrow(out) == 72)
fwrite(out, "coefs_v2_yearFE.csv", bom = TRUE)
cat("coefs_v2_yearFE.csv", nrow(out), "행\n")
print(out[table == "H1" & model == "both", .(version, dep, term, coef = round(coef, 4), se = round(se_cluster, 4), stars, nobs, n_muni)])
print(out[table == "H2", .(version, dep, term, coef = round(coef, 4), se = round(se_cluster, 4), stars, nobs)])
