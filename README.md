# 일본 과소지역 인구 · 공시지가 · 실거래가 패널 (2010–2026)

SEED 한일 비교 연구(고령화 → 부동산 가격)의 **일본 쪽 데이터셋**.
일본 과소지역(過疎地域) 727개 시정촌의 2010~2026년 연도별 **인구(연령·성별)**, **공시지가**, **실거래가**를 같은 단위·같은 행 순서로 정리했다.

## 최종 파일 (`final_result/`)

| 파일 | 내용 | 행 | 열 |
|---|---|---|---|
| `jp_pop_kaso.csv` | 인구 — 총인구, 5세 단위 연령별, 남녀 | 12,359 | 76 |
| `chika_kaso.csv` | 공시지가 — 지점 수, ㎡당 가격 중앙값·평균·최소·최대, 용도별 | 12,359 | 25 |
| `torihiki_kaso.csv` | 실거래가 — 거래 건수, 부동산 종류별 ㎡당 가격 중앙값 | 12,359 | 18 |

- 행 = 시정촌 1곳 × 1년. 727곳 × 17년. 세 파일은 **행 순서·`year`·`muni_code`가 동일**해서 그 두 열로 바로 붙는다.
- 지역 코드는 **2026년 시정촌 코드 기준**으로 통일(합병·승격 반영). 과소지역은 총무성 2022년 4월 목록의 전부과소 713곳 + 간주과소 14곳.
- 열 설명과 원본→열 대응은 [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md), 작업 과정·결정·검사 결과는 [docs/PROCESS.md](docs/PROCESS.md).

## 데이터 출처

| 데이터 | 출처 | 기간 |
|---|---|---|
| 인구 | 총무성 「住民基本台帳に基づく人口、人口動態及び世帯数調査」 시구정촌별 연령계급별 인구(일본인 주민), e-Stat | 2010~2026 (매년) |
| 과소지역 목록 | 총무성 「過疎地域市町村等一覧」 (令和4年4月1日) | 2022 기준 |
| 공시지가 | 국토교통성 国土数値情報 L01 地価公示 | 2010~2026 (매년 1/1) |
| 실거래가 | 국토교통성 不動産情報ライブラリ API XIT001 不動産取引価格情報 | 2010Q1~2026Q1 (분기) |

출처 표기: 「国土数値情報（地価公示データ）（国土交通省）」, 「出典：国土交通省 不動産情報ライブラリ」(PDL 1.0). 인구·과소지역은 e-Stat/総務省 이용약관에 따름.

## 알아둘 한계

- 인구 기준일: 2010~2013은 3월 31일, 2014~는 1월 1일 (`ref_date` 열). 공시지가는 전 기간 1월 1일.
- 80세 이상 세부(80~84 … 100+)는 2015년부터만 있음. 전 기간 비교는 `age_80p`.
- 공시지가: 727곳 중 **299곳은 17년 내내 지점이 없음**(도시계획구역 밖 소규모 町村). 실거래가는 569곳이 17년 전부 있음.
- 2013년 공시지가 용도구분 재편(준공업지·조정구역 내 택지 코드 소멸)으로 2012→2013 사이 구성 변화.
- 실거래가 2026년은 1분기만.
- 고령화율 등 **비율 열은 아직 없음**(한국 쪽 정의에 맞춰 추가 예정). 분석(회귀)은 하지 않았다.

## 재현

```text
python scripts/clean_jp_population.py        # 1단계 인구 양식 통일   ← Population2/
python scripts/type_jp_population.py         # 2단계 행 종류 라벨
python scripts/standardize_jp_population.py  # 3단계 2026 코드 통일
python scripts/filter_kaso.py                # 5단계 과소지역 727곳   ← Kaso(과소지역)/
python scripts/extract_chika_points.py       # ③ 공시지가 GML → 지점 CSV  ← Chika(지가공시)/*.zip
python scripts/build_chika_muni.py           # ③ 집계 → chika_kaso.csv
python scripts/fetch_reinfolib.py            # ② 실거래가 API 수집 (환경변수 REINFOLIB_API_KEY 필요)
python scripts/extract_torihiki_points.py    # ② JSON → 거래 CSV
python scripts/build_torihiki_muni.py        # ② 집계 → torihiki_kaso.csv
```

용량 때문에 저장소에 없는 것: `Reinfolib/raw/`(API 응답 4.3GB), `Chika(지가공시)/*.zip`(225MB), `output/chika_points/`, `output/torihiki_points/`. 받는 법은 [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md)의 각 "출처" 절. 공시지가 zip은 `Chika(지가공시)/SHA256SUMS.txt`로 동일 파일인지 확인할 수 있다.

## 폴더

```text
final_result/        최종 3개
docs/                DATA_GUIDE.md (데이터셋 설명), PROCESS.md (작업 기록)
scripts/             파이프라인 9개 + code_map_2010_2026.csv (코드 대응표)
Population2/         인구 원본 엑셀 17개
Kaso(과소지역)/       과소지역 목록 엑셀
Chika(지가공시)/      공시지가 zip 17개 (저장소엔 해시만)
Reinfolib/raw/       실거래가 API 응답 (저장소엔 없음)
과소지역_매칭/        과소 매칭표, 인구 727곳 파일
output/              중간 산출물 (전국 집계, 2026 코드 패널, 기록용 파일)
```
