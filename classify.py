# -*- coding: utf-8 -*-
"""냉난방(공조)면적 키워드 사전 — 참조 구현.

건축물대장 층별개요의 층기타용도(etc_purps)·층주용도(main_purps_nm) 문자열을
비공조(noncond) / 준공조(semi) / 공조(cond) 로 분류하고, 주차 여부를 함께 돌려준다.

    >>> from classify import classify, classify_row
    >>> classify("지하주차장")
    ('noncond', True)
    >>> classify("사무실")
    ('cond', False)
    >>> classify_row("근린생활시설(120.5㎡)/계단실(12㎡)", "제2종근린생활시설", 132.5)
    [('근린생활시설', 120.5, 'cond', False), ('계단실', 12.0, 'noncond', False)]

CLI:
    python classify.py 주차장 사무실 "창고(냉동)"
"""
import json, os, re, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "keyword_dictionary.json"), encoding="utf-8") as f:
    DICT = json.load(f)

_noncond_re = re.compile("|".join(re.escape(k) for k in DICT["noncond"]))
_semi_re    = re.compile("|".join(re.escape(k) for k in DICT["semi"]))
_park_re    = re.compile("|".join(re.escape(k) for k in DICT["parking"]))

_SPLIT_RE = re.compile(r"[\/,，·;|]+")            # 토큰 구분자
_AREA_RE  = re.compile(r"\((\d+\.?\d*)\s*㎡\)")   # "용도명(123.4㎡)" 괄호 면적
_WS_RE    = re.compile(r"\s+")


def normalize(s):
    """공백 제거 + 소문자화. None/비문자열은 빈 문자열."""
    return _WS_RE.sub("", s).lower() if isinstance(s, str) else ""


def classify(text):
    """문자열 하나를 분류. 반환 (class, is_parking).
    class: 'noncond' | 'semi' | 'cond'  (우선순위 noncond > semi > cond)"""
    t = normalize(text)
    is_park = bool(_park_re.search(t))
    if _noncond_re.search(t):
        return "noncond", is_park
    if _semi_re.search(t):
        return "semi", is_park
    return "cond", is_park


def split_row(etc_purps, main_purps, area):
    """층별개요 한 행 -> [(name, area), ...].
    etc_purps 에 '용도(면적㎡)' 괄호 패턴이 있으면 토큰별 면적으로 분해, 없으면 행 전체를 하나로."""
    e = normalize(etc_purps)
    if "㎡)" in e:
        out = []
        for tok in _SPLIT_RE.split(e):
            m = _AREA_RE.search(tok) if tok else None
            if not m:
                continue
            name = _AREA_RE.sub("", tok).strip()
            if name:
                out.append((name, float(m.group(1))))
        if out:
            return out
    key = e if e else normalize(main_purps)
    try:
        a = float(area) if area not in (None, "") else 0.0
    except (TypeError, ValueError):
        a = 0.0
    return [(key, a)] if key else []


def classify_row(etc_purps, main_purps, area):
    """층별개요 한 행 -> [(name, area, class, is_parking), ...]"""
    return [(n, a, *classify(n)) for n, a in split_row(etc_purps, main_purps, area)]


def aggregate(rows):
    """rows: iterable of (flr_gb_nm, main_purps_nm, etc_purps, area) — 한 건물의 층별개요 행들.
    반환 dict: floor_sum, cond_area, semi_area, noncond_area, parking_area,
               facility_area(=floor_sum-parking), effective_area(지상 & 비주차)"""
    r = dict(floor_sum=0.0, cond_area=0.0, semi_area=0.0, noncond_area=0.0,
             parking_area=0.0, effective_area=0.0)
    for flr_gb, main, etc, area in rows:
        try:
            r["floor_sum"] += float(area) if area not in (None, "") else 0.0
        except (TypeError, ValueError):
            pass
        is_ground = (flr_gb == "지상")
        for _, a, cls, is_park in classify_row(etc, main, area):
            if a <= 0:
                continue
            r[f"{cls}_area"] += a
            if is_park:
                r["parking_area"] += a
            if is_ground and not is_park:
                r["effective_area"] += a
    r["facility_area"] = max(r["floor_sum"] - r["parking_area"], 0.0)
    return r


if __name__ == "__main__":
    args = sys.argv[1:] or ["지하주차장", "사무실", "창고(냉동)", "계단실", "아파트", "발코니"]
    for a in args:
        cls, park = classify(a)
        print(f"{a!r:20s} -> {cls:8s} parking={park}")
    print()
    demo = [("지하", "주차장", "주차장", 300), ("지상", "제2종근린생활시설", "소매점", 200),
            ("지상", "업무시설", "사무실", 200), ("지상", "업무시설", "사무실", 200),
            ("지상", "계단실", "계단실", 20)]
    print("예시 건물 집계:", aggregate(demo))
