"""panel_v3.csv = 1030_interm2/panel_v2.csv (33열) + hedonicB_index.csv 6열. v2 열은 손대지 않음."""
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
p = pd.read_csv(os.path.join(HERE, "..", "1030_interm2", "panel_v2.csv"), dtype={"muni_code": str, "pref_code": str})
h = pd.read_csv(os.path.join(HERE, "hedonicB_index.csv"), dtype={"muni_code": str})
need = ["muni_code", "year", "log_p_land_hedB", "n_land_hedB", "log_p_condo_hedB", "n_condo_hedB", "log_p_land_hedA_nofloor", "n_land_hedA_nofloor"]
assert all(c in h.columns for c in need), [c for c in need if c not in h.columns]
out = p.merge(h[need], on=["muni_code", "year"], how="left")
assert len(out) == 27856 and out.n_land_hedB.notna().all() and list(out.columns[:33]) == list(p.columns)
assert all(out[c].equals(p[c]) for c in p.columns)
out.to_csv(os.path.join(HERE, "panel_v3.csv"), index=False, encoding="utf-8-sig", float_format="%.6f")
print("panel_v3.csv", out.shape, "| v2 33열 동일 확인")
