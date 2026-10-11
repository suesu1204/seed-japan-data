# 일본 과소지역 인구 · 공시지가 · 실거래가 패널 (2010–2026)

SEED 한일 비교 연구(고령화 → 부동산 가격)의 **일본 쪽 데이터셋**.
일본 과소지역(過疎地域) 727개 시정촌의 2010~2026년 연도별 **인구(연령·성별)**, **공시지가**, **실거래가**를 같은 단위·같은 행 순서로 정리했다.

## 최종 파일 (`final_result2/`) — 전국 1,741곳 × 2010~2026

한국 쪽 인구 파일(`korea_population_2010_2025.csv`, 시군구 225곳 전국)과 맞추기 위해 2026-10-11에 **전국 · 시정촌 + 도쿄 23구 단위**(정령시는 시 전체)로 다시 만들었다. 과소지역 여부는 `kaso` 열로 표시한다.

| 파일 | 내용 | 행 | 열 |
|---|---|---|---|
| `jp_pop.csv` | 인구 — 한국 파일과 같은 열 구성: `total_pop`, 유년(0~14)·청년(15~34)·중장년(35~64)·고령(65+)의 인구수와 비율(%), `aging_rate`(=elderly_rate) + `kaso` | 29,597 | 13 |
| `jp_pop_detail.csv` | 인구 원자료 — 5세 단위·남녀 69열 | 29,597 | 71 |
| `chika.csv` | 공시지가 — 지점 수, ㎡당 가격 중앙값·평균·최소·최대, 용도별(주택지·상업지 등 7종) | 29,597 | 21 |
| `torihiki.csv` | 실거래 **건별** 전국 2010Q1~2026Q1, 원본 항목만 (계산 열 없음). **312MB, 깃허브 제외 → 드라이브** | 5,033,013 | 10 |
| `muni_names.csv` | `muni_code` ↔ 도도부현·이름·종류(city/special_ward/town/village)·과소 구분 | 1,741 | 5 |

- 식별 열은 `year`, `muni_code`만. 이름은 `muni_names.csv`로 대조.
- 단위 1,741 = 시 792(정령시 20 포함) + 도쿄 특별구 23 + 정 743 + 촌 183. 17년 완전 균형 패널.
- `kaso`: 全部過疎 713 / みなし過疎 14 / 一部過疎 158 / 非該当 856 (총무성 2022년 4월 목록).
- 이전 버전(과소 727곳만, 집계형 실거래가)은 `final_result/`에 그대로 둠.
- 열 설명과 원본→열 대응은 [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md), 작업 과정은 [docs/PROCESS.md](docs/PROCESS.md).

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
- 비율은 한국 파일 정의(0~14 / 15~34 / 35~64 / 65+, 분모 총인구, %)를 따름. 일본 총인구에는 연령불상자가 포함돼 네 비율 합이 99.8~100%. 증가율 열은 없음(한국 파일에 없음). 분석(회귀)은 하지 않았다.

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
python scripts/build_torihiki_muni.py        # ② 집계 → torihiki_kaso.csv (727곳 버전)
python scripts/build_final.py                # 최종: final_result2/ 전국 1,741곳 (인구·공시지가·실거래 건별)
```

용량 때문에 저장소에 없는 것: `final_result2/torihiki.csv`(312MB, 드라이브), `Reinfolib/raw/`(API 응답 4.3GB), `Chika(지가공시)/*.zip`(225MB), `output/chika_points/`, `output/torihiki_points/`. 받는 법은 [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md)의 각 "출처" 절. 공시지가 zip은 `Chika(지가공시)/SHA256SUMS.txt`로 동일 파일인지 확인할 수 있다.

## 폴더

```text
final_result2/       최종 (전국 1,741곳) 5개
final_result/        이전 버전 (과소 727곳) 3개
docs/                DATA_GUIDE.md (데이터셋 설명), PROCESS.md (작업 기록)
scripts/             파이프라인 10개 + code_map_2010_2026.csv (코드 대응표)
Population2/         인구 원본 엑셀 17개
Kaso(과소지역)/       과소지역 목록 엑셀
Chika(지가공시)/      공시지가 zip 17개 (저장소엔 해시만)
Reinfolib/raw/       실거래가 API 응답 (저장소엔 없음)
과소지역_매칭/        과소 매칭표, 인구 727곳 파일
output/              중간 산출물 (전국 집계, 2026 코드 패널, 기록용 파일)
```
