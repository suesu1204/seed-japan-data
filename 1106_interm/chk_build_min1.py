"""1105_interm 2단계: 거주용 단독주택 가격 열을 panel_v4 에 붙여 panel_v5.csv.
단독주택 정의: Type 宅地(土地と建物) 중 Use == '住宅' (단일 용도 주택만; 共同住宅·住宅、店舗 등 제외).
가격: 연면적당 = trade_price / floor_area_sqm (한국 단독·다가구 실거래가의 연면적 기준과 대응). 대지면적당도 보조로 둠.
연면적 9999(2,000㎡ 이상 상한 코드)·결측·0은 제외. 대지면적 9999는 연면적당 가격과 무관하므로 제외하지 않음(대지면적당 보조 지표에서만 결측 처리). 시정촌·연도 거래 5건 미만은 결측.
입력 house_trades.csv, ../1031_interm/panel_v4.csv   출력 panel_v5.csv (= v4 + n_house, log_p_house, log_p_house_land)
"""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); MIN_N = 1
h = pd.read_csv(os.path.join(HERE, "../1105_interm/house_trades.csv"), dtype={"muni_code": str, "building_year": str, "structure": str, "use": str, "purpose": str})
n0 = len(h)
# 시정촌 코드 통일 (scripts/build_final.py 와 같은 규칙): 합병 코드 연쇄 → 2026 코드, 정령시의 구 → 소속 시
cmap = pd.read_csv(os.path.join(ROOT, "scripts", "code_map_2010_2026.csv"), dtype=str).fillna("")
MP = cmap[cmap.new_code != ""].set_index("old_code").new_code
for _ in range(5):
    hit = h.muni_code.isin(MP.index)
    if not hit.any(): break
    h.loc[hit, "muni_code"] = h.loc[hit, "muni_code"].map(MP)
t26 = pd.read_csv(os.path.join(ROOT, "output", "population_typed", "jp_pop_typed_2026.csv"), dtype={"muni_code": str, "city_code": str}, usecols=["muni_code", "row_type", "city_code"])
W2C = t26[t26.row_type == "ward"].set_index("muni_code").city_code
h["muni_code"] = h.muni_code.where(~h.muni_code.isin(W2C.index), h.muni_code.map(W2C))
res = h[h.use == "住宅"].copy()
print(f"토지+건물 {n0:,} → Use=住宅 {len(res):,} ({len(res)/n0:.1%}) | 그중 Region 住宅地 {(res.region=='住宅地').mean():.1%}")
bad = res.floor_area_sqm.isna() | (res.floor_area_sqm <= 0) | (res.floor_area_sqm == 9999) | (res.trade_price <= 0)
print("제외(연면적 결측/0/9999, 가격 0 이하):", int(bad.sum()))
res = res[~bad].copy()
res["pp_floor"] = res.trade_price / res.floor_area_sqm
res["pp_land"] = res.trade_price / res.area_sqm.where(res.area_sqm != 9999)
g = res.groupby(["year", "muni_code"]).agg(n_house=("pp_floor", "size"), med_floor=("pp_floor", "median"), med_land=("pp_land", "median")).reset_index()
# 단독주택+아파트 합산(주거용 주택): 단독주택 연면적당 + 아파트 전용면적당 거래를 한 풀로 묶어 중앙값. 둘 다 건물 바닥면적당 가격.
c = pd.read_csv(os.path.join(ROOT, "final_result2", "torihiki.csv"), dtype={"muni_code": str, "building_year": str}, usecols=["year", "muni_code", "type", "trade_price", "area_sqm"])
c = c[(c.type == "中古マンション等") & (c.year <= 2025) & (c.area_sqm != 9999)].copy(); c["pp_floor"] = c.trade_price / c.area_sqm
pool = pd.concat([res[["year", "muni_code", "pp_floor"]].assign(kind="house"), c[["year", "muni_code", "pp_floor"]].assign(kind="condo")])
gr = pool.groupby(["year", "muni_code"]).agg(n_resi=("pp_floor", "size"), med_resi=("pp_floor", "median"), share_house_resi=("kind", lambda k: (k == "house").mean())).reset_index()
g = g.merge(gr, on=["year", "muni_code"], how="outer")
# 점검용: 아파트도 거래 자료에서 MIN_N 기준으로 다시 집계해 기존 열을 덮어씀
gc = c.groupby(["year", "muni_code"]).agg(n_condo_new=("pp_floor", "size"), med_condo=("pp_floor", "median")).reset_index()
g = g.merge(gc, on=["year", "muni_code"], how="outer")
print(f"아파트 거래 {len(c):,} + 단독주택 {len(res):,} = 합산 {len(pool):,}")
p = pd.read_csv(os.path.join(ROOT, "1031_interm", "panel_v4.csv"), dtype={"muni_code": str, "pref_code": str})
assert res.muni_code.isin(set(p.muni_code)).all(), res[~res.muni_code.isin(set(p.muni_code))].muni_code.value_counts().head()
out = p.merge(g, on=["year", "muni_code"], how="left")
assert len(out) == len(p)
out["n_house"] = out.n_house.fillna(0).astype(int); out["n_resi"] = out.n_resi.fillna(0).astype(int)
out["n_condo"] = out.n_condo_new.fillna(0).astype(int); out["log_p_condo"] = np.log(out.med_condo.where(out.n_condo >= MIN_N))
out["log_p_resi"] = np.log(out.med_resi.where(out.n_resi >= MIN_N)); out.loc[out.n_resi < MIN_N, "share_house_resi"] = np.nan
out["log_p_house"] = np.log(out.med_floor.where(out.n_house >= MIN_N))
out["log_p_house_land"] = np.log(out.med_land.where(out.n_house >= MIN_N))
out = out.drop(columns=["med_floor", "med_land", "med_resi", "med_condo", "n_condo_new"])
assert out.n_house.sum() == len(res) and out.n_resi.sum() == len(pool)
out.to_csv(os.path.join(HERE, "panel_v5_min1.csv"), index=False, encoding="utf-8-sig", float_format="%.6f")
print("panel_v5_min1.csv", out.shape)
print("관측치(5건 이상 칸):", {"house": int(out.log_p_house.notna().sum()), "condo": int(out.log_p_condo.notna().sum()), "resi": int(out.log_p_resi.notna().sum()), "land": int(out.log_p_land.notna().sum())},
      "| 전체 칸", len(out))
print("단독주택 연면적당 가격(엔/㎡) 중앙값 분포:", np.exp(out.log_p_house).describe()[["25%", "50%", "75%"]].round(0).to_dict())
print("한 번도 값 없는 시정촌:", int((out.groupby("muni_code").log_p_house.count() == 0).sum()))
print("합산 칸의 단독주택 비중: 중앙값", round(out.share_house_resi.median(), 3), "| 아파트 거래 0인 칸 비율", round((out.share_house_resi == 1).mean() / out.share_house_resi.notna().mean(), 3))
