# 1031_bonus. 추가 확인 7종. 소득 없음, 2010~2025 전체. 시정촌 + 현×연도 (차분: 현×구간), 시정촌 군집.
# 종속변수 4: 중앙값 v2 토지·아파트, 헤도닉A 토지(하한 없음)·아파트. 표 H1(3) + H2(중장년 기준, 합·차)
# 0 base(재추정, 기존 결과와 동일해야 함) 1 아파트 표본 토지 2 규모별 3 건수 하한·가중 4 고령 65~74/75+ 분리 5 거래량 6 10년 차분 7 1년 차분
# 입력 ../1031_interm/panel_v4.csv  출력 coefs_bonus.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1031_interm/panel_v4.csv", colClasses = list(character = c("muni_code", "pref_code")))
DEPS <- c(land = "log_p_land", condo = "log_p_condo", land_hedA = "log_p_land_hedA_nofloor", condo_hedA = "log_p_condo_hed")
CNT  <- c(land = "n_land", condo = "n_condo", land_hedA = "n_land_hedA_nofloor", condo_hedA = "n_condo_hed")
for (d in names(DEPS)) p[, paste0("logn_", d) := fifelse(get(CNT[[d]]) >= 1, log(get(CNT[[d]])), NA_real_)]
LOGN <- setNames(paste0("logn_", names(DEPS)), names(DEPS))
VARS <- c(unname(DEPS), "log_pop", "child_rate", "youth_rate", "middle_rate", "elderly_rate", "share_65_74", "share_75p", unname(LOGN))

# 차분: 연도 쌍마다 뒤 − 앞. 건수는 두 끝점의 최소값(가중용)
diffs <- function(dat, pairs) rbindlist(lapply(pairs, function(yy) {
  m <- merge(dat[year == yy[1]], dat[year == yy[2]], by = "muni_code", suffixes = c("_0", "_1"))
  out <- m[, .(muni_code, pref_code = pref_code_1, period = paste0(yy[1], "_", yy[2]), size_group = size_group_1)]
  for (v in VARS) out[, (v) := m[[paste0(v, "_1")]] - m[[paste0(v, "_0")]]]
  for (d in names(DEPS)) out[, (CNT[[d]]) := pmin(m[[paste0(CNT[[d]], "_0")]], m[[paste0(CNT[[d]], "_1")]])]
  out }))
pairs5 <- list(c(2010, 2015), c(2015, 2020), c(2020, 2025)); pairs10 <- list(c(2010, 2020), c(2015, 2025)); pairs1 <- lapply(2010:2024, function(y) c(y, y + 1))
ld5 <- diffs(p, pairs5)

rows <- list()
est <- function(check, sub, version, dat, deps = names(DEPS), split = FALSE, dep_of = DEPS, w = FALSE) {
  fe <- if (version == "level") "muni_code + pref_code^year" else "pref_code^period"
  eld <- if (split) c("share_65_74", "share_75p") else "elderly_rate"
  specs <- list(H1_pop_only = "log_pop", H1_aging_only = eld, H1_both = c("log_pop", eld), H2_ref_middle = c("log_pop", "child_rate", "youth_rate", eld))
  for (d in deps) { y <- dep_of[[d]]; dd <- dat[!is.na(dat[[y]])]
    for (s in names(specs)) {
      f <- as.formula(paste(y, "~", paste(specs[[s]], collapse = " + "), "|", fe))
      m <- tryCatch(if (w) feols(f, data = dd, cluster = ~muni_code, weights = as.formula(paste0("~", CNT[[d]]))) else feols(f, data = dd, cluster = ~muni_code),
                    error = function(e) { cat("SKIP", check, sub, version, d, s, conditionMessage(e), "\n"); NULL })
      if (is.null(m)) next
      ct <- coeftable(m); tab <- sub("_.*", "", s); model <- sub("^H[12]_", "", s)
      add <- function(term, est, se) rows[[length(rows) + 1]] <<- data.table(check = check, sub = as.character(sub), version = version, dep = d, table = tab, model = model, term = term,
        coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = nobs(m), n_muni = uniqueN(dd$muni_code[obs(m)]))
      for (term in rownames(ct)) add(term, ct[term, 1], ct[term, 2])
      if (tab == "H2") { b <- coef(m); V <- vcov(m)
        for (nm in c("child_plus_elderly", "child_minus_elderly")) { cv <- setNames(rep(0, length(b)), names(b)); cv["child_rate"] <- 1; cv[eld] <- if (nm == "child_plus_elderly") 1 else -1
          add(nm, sum(cv * b), sqrt(as.numeric(t(cv) %*% V %*% cv))) } }
    } } }

est("0_base", "", "level", p); est("0_base", "", "ld5", ld5)
cm <- unique(p[!is.na(log_p_condo), muni_code])
est("1_condo_sample", paste0(length(cm), "곳"), "level", p[muni_code %in% cm], deps = c("land", "land_hedA")); est("1_condo_sample", paste0(length(cm), "곳"), "ld5", ld5[muni_code %in% cm], deps = c("land", "land_hedA"))
for (g in 1:4) { est("2_size", g, "level", p[size_group == g]); est("2_size", g, "ld5", ld5[size_group == g]) }
for (k in c(10, 20)) { pk <- copy(p); for (d in names(DEPS)) pk[get(CNT[[d]]) < k, (DEPS[[d]]) := NA_real_]
  est("3_min_n", paste0("n>=", k), "level", pk); est("3_min_n", paste0("n>=", k), "ld5", diffs(pk, pairs5)) }
est("3_weighted", "건수 가중", "level", p, w = TRUE); est("3_weighted", "건수 가중", "ld5", ld5, w = TRUE)
est("4_age_split", "65~74 / 75+", "level", p, split = TRUE); est("4_age_split", "65~74 / 75+", "ld5", ld5, split = TRUE)
est("5_volume", "log 건수", "level", p, dep_of = LOGN); est("5_volume", "log 건수", "ld5", ld5, dep_of = LOGN)
est("6_ld10", "2010→20, 15→25", "ld10", diffs(p, pairs10))
est("7_fd1", "1년 차분 15구간", "fd1", diffs(p, pairs1))
out <- rbindlist(rows); fwrite(out, "coefs_bonus.csv", bom = TRUE); cat("coefs_bonus.csv", nrow(out), "행\n")
print(out[check == "0_base" & model == "both" & term == "elderly_rate", .(version, dep, coef = round(coef, 4), se = round(se_cluster, 4), nobs)])
