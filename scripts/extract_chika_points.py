"""③-1: 国土数値情報 L01(地価公示) GML → 연도별 지점 CSV 17개.

입력: Chika(지가공시)/L01-YY_GML.zip (2010~2026)
출력: output/chika_points/chika_YYYY.csv   (지점 1개 = 1행)

연도별 태그 경로(LandPrice 기준 상대 경로)는 아래 CFG에 명시한다. 경로가 없으면 추측하지 않고 멈춘다.
"""
import csv, glob, os, re, struct, zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Chika(지가공시)")
OUT = os.path.join(ROOT, "output", "chika_points")
COLS = ["year", "muni_code", "use_code", "seq", "price_per_sqm", "acreage_sqm", "current_use", "lon", "lat"]
# city_planning은 뺐다: 2010~2017은 여러 법규제가 한 태그에 섞여 있어 2018+의 urbanPlanningArea와 해석 없이 대응 불가 (README §7)
# 용도구분 코드 (reinfolib XPT002 API 설명서 useCategoryCode): 00 住宅地, 03 宅地見込地, 05 商業地, 07 準工業地,
# 09 工業地, 10 市街化調整区域内の現況宅地, 13 市街化調整区域内の現況林地. GML에는 3자리(000…)로 들어 있음.
USE_CODES = {"000", "003", "005", "007", "009", "010", "013"}

# 경로 표기: LandPrice 바로 아래 자손을 '/'로 이어 씀.
STD = dict(code="administrativeAreaCode", idx="representedLandCode/RepresentedLandCode/indexNumber",
           seq="representedLandCode/RepresentedLandCode/sequenceNumber", year="year/TimeInstant/timePosition",
           pos="position", price="postedLandPrice", acreage="acreage", use="currentUse")
CFG = {y: dict(STD) for y in [2010, 2011] + list(range(2014, 2024))}
CFG[2012] = dict(code="aac", idx="rlc/RepresentedLandCode/idn", seq="rlc/RepresentedLandCode/rls",
                 year="ye3/TimeInstant/timePosition", pos="pos", price="plp", acreage="ac1", use="pu1")
CFG[2013] = dict(STD, idx="rlc/representedLandCode/indexNumber", seq="rlc/representedLandCode/sequenceNumber")
for y in [2024, 2025, 2026]:
    CFG[y] = dict(STD, code="representedLandCode/administrativeAreaCode", idx="representedLandCode/indexNumber",
                  seq="representedLandCode/sequenceNumber")


def strip(tag):
    return tag.split("}")[-1]


def dbf_count(z):
    m = [n for n in z.namelist() if n.lower().endswith(".dbf")][0]
    return struct.unpack("<I", z.open(m).read(8)[4:8])[0]


def paths(el):
    """LandPrice의 모든 자손을 (상대경로, 텍스트, 속성) 목록으로."""
    out = []
    def walk(e, pre):
        for c in e:
            p = (pre + "/" if pre else "") + strip(c.tag)
            out.append((p, (c.text or "").strip(), c.attrib))
            walk(c, p)
    walk(el, "")
    return out


def extract(year, zpath):
    cfg = CFG[year]
    z = zipfile.ZipFile(zpath)
    xml = [n for n in z.namelist() if n.lower().endswith(".xml") and "META" not in n.upper()][0]
    points, rows = {}, []
    for ev, el in ET.iterparse(z.open(xml), events=("end",)):
        tag = strip(el.tag)
        if tag == "Point":
            pid = next(v for k, v in el.attrib.items() if strip(k) == "id")
            pos = next(c for c in el.iter() if strip(c.tag) in ("pos", "position")).text.split()  # 2013만 gml:position
            points[pid] = (float(pos[1]), float(pos[0]))  # "위도 경도" 순 → (lon, lat)
            el.clear()
        elif tag == "LandPrice":
            ps = paths(el)
            vals = {}
            for p, t, _ in ps:
                vals.setdefault(p, []).append(t)
            def one(key):
                p = cfg[key]
                assert p in vals and len(vals[p]) == 1 and vals[p][0] != "", (year, key, p, vals.get(p))
                return vals[p][0]
            href = next((a for p, _, a in ps if p == cfg["pos"]), None)
            assert href is not None, (year, "pos", cfg["pos"])
            ref = next(v for k, v in href.items() if strip(k) == "href").lstrip("#")
            assert ref in points, (year, "point not found", ref)
            uses = vals.get(cfg["use"], [])
            assert uses, (year, "use", cfg["use"])
            rows.append(dict(
                year=int(one("year")), muni_code=one("code"), use_code=one("idx"), seq=one("seq"),
                price_per_sqm=int(one("price")), acreage_sqm=one("acreage"),
                current_use=",".join(uses),
                lon=points[ref][0], lat=points[ref][1],
            ))
            el.clear()
    return rows, dbf_count(z)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for zpath in sorted(glob.glob(os.path.join(SRC, "L01-??_GML.zip"))):
        year = 2000 + int(re.search(r"L01-(\d\d)", zpath).group(1))
        rows, n_dbf = extract(year, zpath)
        # 검사
        assert len(rows) == n_dbf, (year, len(rows), n_dbf)
        assert all(r["year"] == year for r in rows), year
        assert all(re.fullmatch(r"\d{5}", r["muni_code"]) for r in rows), year
        assert all(r["price_per_sqm"] > 0 for r in rows), year
        bad = {r["use_code"] for r in rows} - USE_CODES
        assert not bad, (year, "unknown use_code", bad)
        with open(os.path.join(OUT, f"chika_{year}.csv"), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
        uc = {}
        for r in rows: uc[r["use_code"]] = uc.get(r["use_code"], 0) + 1
        print(f"{year}: {len(rows):6d} points | use_code counts={dict(sorted(uc.items()))}")
    print("saved →", OUT)
