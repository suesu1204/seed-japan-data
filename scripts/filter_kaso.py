"""5단계: 3단계 분석용 패널에서 과소지역 시정촌만 골라낸다.

입력: output/jp_pop_2026basis.csv, Kaso(과소지역)/000807167.xlsx (総務省 過疎地域市町村等一覧, R4.4.1)
출력: 과소지역_매칭/kaso_match.csv        885곳 ↔ 우리 코드 매칭표 (과소구분은 여기에만 기록)
      과소지역_매칭/jp_pop_kaso.csv        (a) 全部過疎 + みなし過疎 727곳 × 17년
      과소지역_매칭/jp_pop_kaso_all885.csv (b) 885곳 × 17년, 참고용
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(ROOT, "output", "jp_pop_2026basis.csv")
KASO = os.path.join(ROOT, "Kaso(과소지역)", "000807167.xlsx")
OUT_MATCH = os.path.join(ROOT, "과소지역_매칭", "kaso_match.csv")
OUT_A = os.path.join(ROOT, "과소지역_매칭", "jp_pop_kaso.csv")
OUT_B = os.path.join(ROOT, "과소지역_매칭", "jp_pop_kaso_all885.csv")


def norm(s):
    return s.str.replace("ケ", "ヶ")


k = pd.read_excel(KASO, sheet_name="市町村数", header=None, dtype=str).iloc[4:, [0, 1, 2, 3, 4]]
k.columns = ["no", "pref", "kaso_name", "kaso_kind", "partial_area"]
k = k[k.no.astype(float).between(1, 885)].reset_index(drop=True)
assert len(k) == 885 and k.kaso_kind.value_counts().to_dict() == {"全部過疎": 713, "一部過疎": 158, "みなし過疎": 14}

panel = pd.read_csv(PANEL, dtype={"muni_code": str, "city_code": str})
p26 = panel[panel.year == 2026][["pref", "muni", "muni_code", "row_type"]].copy()
p26["key"] = norm(p26.muni.str.replace(r"^.+郡", "", regex=True))  # 郡 접두 제거 + ケ→ヶ
k["key"] = norm(k.kaso_name)

match = k.merge(p26, on=["pref", "key"], how="left").drop(columns="key")
assert match.muni_code.notna().all(), match[match.muni_code.isna()]
assert not match.muni_code.duplicated().any()
assert match.row_type.value_counts().to_dict() == {"town": 449, "city": 311, "village": 125}
match = match[["no", "pref", "kaso_name", "kaso_kind", "partial_area", "muni_code", "muni", "row_type"]]
os.makedirs(os.path.dirname(OUT_MATCH), exist_ok=True)
match.to_csv(OUT_MATCH, index=False, encoding="utf-8-sig")

codes_a = set(match.loc[match.kaso_kind.isin(["全部過疎", "みなし過疎"]), "muni_code"])
codes_b = set(match.muni_code)
out_a = panel[panel.muni_code.isin(codes_a)]
out_b = panel[panel.muni_code.isin(codes_b)]
assert len(codes_a) == 727 and len(out_a) == 727 * 17, len(out_a)
assert len(codes_b) == 885 and len(out_b) == 885 * 17, len(out_b)
assert (out_a.groupby("muni_code").size() == 17).all() and (out_b.groupby("muni_code").size() == 17).all()
assert not out_b.duplicated(["year", "muni_code"]).any() and codes_a <= codes_b
out_a.to_csv(OUT_A, index=False, encoding="utf-8-sig")
out_b.to_csv(OUT_B, index=False, encoding="utf-8-sig")

# 3단계 대응표의 변경이 과소지역에 걸린 곳 (README 기록용)
cmap = pd.read_csv(os.path.join(ROOT, "scripts", "code_map_2010_2026.csv"), dtype=str).fillna("")
hit = cmap[cmap.new_code.isin(codes_b)].merge(match[["muni_code", "kaso_kind"]], left_on="new_code", right_on="muni_code")
print(hit[["old_code", "old_name", "new_code", "new_name", "note", "kaso_kind"]].to_string(index=False))
print(f"(a) {len(codes_a)} × 17 = {len(out_a)} | (b) {len(codes_b)} × 17 = {len(out_b)}")
