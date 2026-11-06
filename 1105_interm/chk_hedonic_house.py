"""진단: 단독주택 헤도닉용 거래 파일. Use=住宅, 연면적·대지 9999 제외, 시정촌 코드 통일(01과 동일). 출력 house_hed_trades.csv"""
import os, re, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
h = pd.read_csv(os.path.join(HERE, "house_trades.csv"), dtype={"muni_code": str, "building_year": str, "structure": str, "use": str, "purpose": str})
cmap = pd.read_csv(os.path.join(ROOT, "scripts", "code_map_2010_2026.csv"), dtype=str).fillna(""); MP = cmap[cmap.new_code != ""].set_index("old_code").new_code
for _ in range(5):
    hit = h.muni_code.isin(MP.index)
    if not hit.any(): break
    h.loc[hit, "muni_code"] = h.loc[hit, "muni_code"].map(MP)
t26 = pd.read_csv(os.path.join(ROOT, "output", "population_typed", "jp_pop_typed_2026.csv"), dtype={"muni_code": str, "city_code": str}, usecols=["muni_code", "row_type", "city_code"])
W2C = t26[t26.row_type == "ward"].set_index("muni_code").city_code; h["muni_code"] = h.muni_code.where(~h.muni_code.isin(W2C.index), h.muni_code.map(W2C))
r = h[(h.use == "住宅") & h.floor_area_sqm.notna() & (h.floor_area_sqm != 9999) & (h.area_sqm != 9999) & (h.trade_price > 0)].copy()
by = r.building_year.fillna("").replace({"戦前": "1945年"}).str.extract(r"^(\d{4})年$")[0].astype(float)
r["age"] = (r.year - by).clip(lower=0); r["age_na"] = r.age.isna().astype(int); r["age"] = r.age.fillna(r.age.mean())
r["struct"] = r.structure.fillna("불명").where(r.structure.isin(["木造", "軽量鉄骨造", "鉄骨造", "ＲＣ"]) | r.structure.isna(), "기타")
r["ln_p"] = np.log(r.trade_price / r.floor_area_sqm); r["ln_floor"] = np.log(r.floor_area_sqm); r["ln_land"] = np.log(r.area_sqm)
r[["year", "muni_code", "ln_p", "ln_floor", "ln_land", "age", "age_na", "struct"]].to_csv(os.path.join(HERE, "house_hed_trades.csv"), index=False, encoding="utf-8-sig")
print(len(r), "건 | 연령 빈칸", int(r.age_na.sum()), "| 연령 평균", round(r.age.mean(), 1), "| 구조:", r.struct.value_counts().to_dict())
