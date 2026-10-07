"""②-0: reinfolib XIT001(不動産取引価格情報) API로 원본 JSON 수집.

범위: 2010~2026년 × 1~4분기 × 도도부현 01~47, priceClassification=01(取引価格)
저장: Reinfolib/raw/XIT001_{year}_{quarter}_{area}.json  (응답 바이트 그대로)
키:   환경변수 REINFOLIB_API_KEY (파일에 적지 않음)
이미 있는 파일은 건너뛰므로 중단 후 재실행하면 이어서 받는다.
"""
import json, os, sys, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "Reinfolib", "raw")
URL = "https://www.reinfolib.mlit.go.jp/ex-api/external/XIT001"
KEY = os.environ["REINFOLIB_API_KEY"]
YEARS = range(2010, 2027)
AREAS = [f"{i:02d}" for i in range(1, 48)]
SLEEP = 1.0          # 요청 간격(초)

os.makedirs(RAW, exist_ok=True)
log = open(os.path.join(RAW, "_fetch_log.txt"), "a", encoding="utf-8")
done = skipped = empty = 0
for year in YEARS:
    for q in (1, 2, 3, 4):
        for area in AREAS:
            path = os.path.join(RAW, f"XIT001_{year}_{q}_{area}.json")
            if os.path.exists(path):
                skipped += 1
                continue
            for attempt in range(6):
                try:
                    r = requests.get(URL, params={"year": year, "quarter": q, "area": area, "priceClassification": "01"},
                                     headers={"Ocp-Apim-Subscription-Key": KEY}, timeout=180)
                except requests.RequestException as e:
                    r = None; err = str(e)
                if r is not None and r.status_code == 200:
                    body = json.loads(r.content.decode("utf-8-sig"))
                    assert body.get("status") == "OK", (year, q, area, body.get("status"))
                    open(path, "wb").write(r.content)
                    n = len(body.get("data", []))
                    empty += (n == 0); done += 1
                    log.write(f"{year}\t{q}\t{area}\t{n}\n"); log.flush()
                    break
                if r is not None and r.status_code == 404 and "検索結果がありません" in r.text:
                    log.write(f"{year}\t{q}\t{area}\tNOT_PUBLISHED\n"); log.flush()
                    break  # 아직 공개 전 분기 (파일 안 만듦)
                wait = 10 * (attempt + 1)
                msg = err if r is None else f"HTTP {r.status_code} {r.text[:120]}"
                print(f"retry {year} q{q} {area}: {msg} -> {wait}s", file=sys.stderr)
                time.sleep(wait)
            else:
                raise SystemExit(f"포기: {year} q{q} {area}")
            time.sleep(SLEEP)
    print(f"{year} 완료 (누적 받음 {done}, 건너뜀 {skipped}, 빈 응답 {empty})", flush=True)
print("전부 완료")
