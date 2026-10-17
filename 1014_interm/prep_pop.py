"""인구 전처리 (2026-10-14 임시 실행용).

입력: final_result2/jp_pop.csv  (전국 1,741곳 × 2010~2026, 한국 파일과 같은 열 + kaso)
출력: 1014_interm/jp_pop.csv               입력 그대로 복사
      1014_interm/jp_pop_preprocessed.csv  2010~2025만, log_total_pop·kaso_dummy 추가

규칙 (팀 결정 2026-10-14)
- 고령화율은 현재 열(aging_rate = 65세 이상 비중, %) 그대로
- log(총인구) 추가 (선행연구: Takáts 2012, Saita et al. 2016)
- kaso_dummy = 1 if 全部過疎 or みなし過疎 (시정촌 전체가 과소), else 0
- 2026년 제외 (실거래가와 기간 맞춤)
"""
import os
import shutil
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))

src = os.path.join(ROOT, "final_result2", "jp_pop.csv")
shutil.copy(src, os.path.join(HERE, "jp_pop.csv"))

p = pd.read_csv(src, dtype={"muni_code": str})
pre = p[p.year <= 2025].copy()
pre["log_total_pop"] = np.log(pre.total_pop)
pre["kaso_dummy"] = pre.kaso.isin(["全部過疎", "みなし過疎"]).astype(int)
assert len(pre) == 1741 * 16 and pre.kaso_dummy.sum() == 727 * 16
pre.to_csv(os.path.join(HERE, "jp_pop_preprocessed.csv"), index=False, encoding="utf-8-sig")
print("전처리:", pre.shape, "| 열:", list(pre.columns))
print(pre[["aging_rate", "log_total_pop", "kaso_dummy"]].describe().T[["count", "mean", "min", "50%", "max"]].round(2).to_string())
