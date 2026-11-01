# 1101 추가 확인. (1) 고령≥35%에서 아파트 거래 있는 시정촌 목록 + 리조트 플래그 (2) 리조트 제외 B (3) B + log_pop² (4) B + 규모그룹×연도 FE
# 입력 ../1031_interm/panel_v4.csv, muni_names.csv  출력 checks_condo_ge35.csv, coefs_checks.csv
suppressPackageStartupMessages({ library(data.table); library(fixest) })
p <- fread("../1031_interm/panel_v4.csv", colClasses = list(character = c("muni_code", "pref_code")))
nm <- fread("muni_names.csv", colClasses = "character"); p <- merge(p, nm, by = "muni_code", all.x = TRUE)
DEPS <- c(land = "log_p_land", condo = "log_p_condo", land_hedA = "log_p_land_hedA_nofloor", condo_hedA = "log_p_condo_hed")
K1 <- 28; K2 <- 35
p[, `:=`(s2 = pmax(elderly_rate - K1, 0), s3 = pmax(elderly_rate - K2, 0), lp2 = log_pop^2)]
# (1) 목록
g <- p[elderly_rate >= K2 & !is.na(log_p_condo), .(n_years = .N, n_condo_total = sum(n_condo), pop2010 = pop2010[1], elderly_mean = round(mean(elderly_rate), 1), elderly_max = round(max(elderly_rate), 1)), by = .(muni_code, muni_name)][order(-n_condo_total)]
# 리조트 플래그: 이름 기준 수작업 (온천·스키·별장지). 판단은 작성자(Claude) 것, 목록에 남겨 검토 가능하게 함
RESORT <- c("熱海市", "伊東市", "湯沢町", "箱根町", "軽井沢町", "草津町", "那須町", "白浜町", "山中湖村", "野沢温泉村", "妙高市", "下田市", "東伊豆町", "河津町", "南伊豆町", "西伊豆町", "伊豆市", "伊豆の国市", "熱海", "鳴沢村", "富士河口湖町", "日光市", "嬬恋村", "みなかみ町", "白馬村", "大町市", "蓼科", "茅野市", "志摩市", "鳥羽市", "指宿市", "由布市", "別府市", "登別市", "洞爺湖町", "ニセコ町", "倶知安町", "留寿都村", "高山村", "北塩原村", "猪苗代町", "いわき市", "勝浦市", "鴨川市", "館山市", "南房総市", "御宿町", "一宮町", "逗子市", "葉山町", "真鶴町", "湯河原町", "淡路市", "洲本市", "南あわじ市", "宮古島市", "石垣市", "恩納村", "本部町", "読谷村")
g[, resort := as.integer(sapply(muni_name, function(x) any(sapply(RESORT, function(r) grepl(r, x, fixed = TRUE)))))]
fwrite(g, "checks_condo_ge35.csv", bom = TRUE)
cat("고령≥35% & 아파트 거래 행:", nrow(p[elderly_rate >= K2 & !is.na(log_p_condo)]), " 시정촌:", nrow(g), " 그중 리조트 플래그:", sum(g$resort), " (건수 비중", round(100 * sum(g[resort == 1, n_condo_total]) / sum(g$n_condo_total)), "%)\n")
print(g[1:25, .(muni_name, n_years, n_condo_total, pop2010, elderly_mean, resort)])
# (2)~(4)
rows <- list()
add <- function(check, dep, term, est, se, n) rows[[length(rows) + 1]] <<- data.table(check = check, dep = dep, term = term, coef = est, se_cluster = se, p = 2 * pnorm(-abs(est / se)), nobs = n)
combo <- function(m, cv) { b <- coef(m); V <- vcov(m); v <- setNames(rep(0, length(b)), names(b)); v[names(cv)] <- cv; c(sum(v * b), sqrt(as.numeric(t(v) %*% V %*% v))) }
runB <- function(check, dat, extra = "", fe = "muni_code + pref_code^year") for (d in names(DEPS)) {
  m <- feols(as.formula(paste(DEPS[[d]], "~ elderly_rate + s2 + s3 + log_pop", extra, "|", fe)), dat, cluster = ~muni_code); ct <- coeftable(m); n <- nobs(m)
  add(check, d, "slope_lt28", ct["elderly_rate", 1], ct["elderly_rate", 2], n)
  r <- combo(m, c(elderly_rate = 1, s2 = 1)); add(check, d, "slope_28_35", r[1], r[2], n)
  r <- combo(m, c(elderly_rate = 1, s2 = 1, s3 = 1)); add(check, d, "slope_ge35", r[1], r[2], n)
  add(check, d, "n_ge35", sum(dat[[DEPS[[d]]]][obs(m)] > -Inf & dat$elderly_rate[obs(m)] >= K2, na.rm = TRUE), NA_real_, n)
  w <- wald(m, "^s2$|^s3$", print = FALSE); add(check, d, "wald_equal_slopes_p", w$p, NA_real_, n)
}
runB("0_base", p)
runB("1_no_resort", p[!muni_code %in% g[resort == 1, muni_code]])
runB("2_logpop_sq", p, extra = "+ lp2")
runB("3_sizegroup_year", p, fe = "muni_code + pref_code^year + size_group^year")
out <- rbindlist(rows); fwrite(out, "coefs_checks.csv", bom = TRUE); cat("coefs_checks.csv", nrow(out), "행\n")
