# 냉난방(공조)면적 산출용 키워드 사전
### Conditioned-Area Keyword Dictionary for Korean Building Register (건축물대장 층별개요)

건축물대장 **층별개요**의 층기타용도(`etc_purps`)·층주용도(`main_purps_nm`) 문자열을 근거로
각 층(또는 층 내 공간)을 **비공조 / 준공조 / 공조**로 분류하기 위한 키워드 사전과 참조 구현입니다.
성균관대학교에서 전국 6,929,716동의 냉난방면적(`cond_area`) 산출에 사용한 사전 그대로입니다.

| 항목 | 내용 |
|---|---|
| 사전 버전 | v1.0.0 (사전 확정일 2026-06-08, 공개 2026-09-07) |
| 키워드 수 | 비공조 152 · 준공조 34 · (주차계열 11, 비공조의 부분집합) |
| 매칭 방식 | 공백 제거·소문자화 후 **부분 문자열(substring)** 매칭 |
| 우선순위 | 비공조 > 준공조 > 그 외 전부 공조 |

## 파일

| 파일 | 설명 |
|---|---|
| `keyword_dictionary.csv` | 배포용 표 (no, keyword, class, is_parking, match_type, priority). UTF-8 BOM, 엑셀에서 바로 열림 |
| `keyword_dictionary.json` | 프로그램용. `noncond`, `semi`, `parking` 리스트 + 메타 |
| `classify.py` | 참조 구현 (분류·행 분해·건물 집계). 의존성 없음, Python 3.8+ |
| `CHANGELOG.md` | 버전 이력 |

## 분류 규칙

1. 층별개요 한 행의 `etc_purps`를 본다. 비어 있으면 `main_purps_nm`을 쓴다.
2. `"용도명(123.4㎡)"` 괄호 면적 패턴이 있으면 `/ , · ; |` 로 토큰을 나눠 토큰별로 판정한다. 없으면 행 전체를 하나의 토큰으로 보고 행 면적(`area`)을 쓴다.
3. 토큰을 공백 제거·소문자화한 뒤
   - **비공조 키워드**가 하나라도 포함되면 → `noncond` (주차·계단·승강기·기계실·화장실·탱크·축사·옥외 등)
   - 아니면 **준공조 키워드**가 포함되면 → `semi` (창고·공장·냉장·발코니·현관·홀 등)
   - 둘 다 아니면 → `cond` (주거·업무·상업·교육·의료·숙박 등 나머지 전부)
4. 주차 키워드(주차·차고·램프·필로티 등)가 포함되면 `is_parking = Y`. 시설면적(전체 − 주차)·용면적(지상 비주차) 산출에 쓴다.

건물 단위 집계:

```
cond_area    = Σ cond 토큰 면적          ← 냉난방(공조)면적
semi_area    = Σ semi 토큰 면적          ← 별도 집계 (필요 시 cond에 합산)
noncond_area = Σ noncond 토큰 면적
```

준공조는 "냉난방을 부분적·간헐적으로 하거나 산업용 냉장 등 판단이 갈리는 공간"이라 공조면적에 합산하지 않고 따로 둡니다. 보수적으로 잡으려면 `cond_area`만, 넓게 잡으려면 `cond_area + semi_area`를 쓰면 됩니다.

## 사용 예

```python
from classify import classify, classify_row, aggregate

classify("지하주차장")        # ('noncond', True)
classify("창고(냉동)")        # ('semi', False)
classify("사무실")            # ('cond', False)

classify_row("근린생활시설(120.5㎡)/계단실(12㎡)", "제2종근린생활시설", 132.5)
# [('근린생활시설', 120.5, 'cond', False), ('계단실', 12.0, 'noncond', False)]

rows = [("지하", "주차장", "주차장", 300), ("지상", "제2종근린생활시설", "소매점", 200),
        ("지상", "업무시설", "사무실", 400), ("지상", "계단실", "계단실", 20)]
aggregate(rows)
# {'floor_sum': 920, 'cond_area': 600, 'semi_area': 0, 'noncond_area': 320,
#  'parking_area': 300, 'effective_area': 620, 'facility_area': 620}
```

pandas 로 직접 쓰려면 `keyword_dictionary.json`의 리스트를 정규식으로 합쳐 `str.contains` 하면 같은 결과가 나옵니다:

```python
import json, re, pandas as pd
d = json.load(open("keyword_dictionary.json", encoding="utf-8"))
rx = lambda ks: "|".join(map(re.escape, ks))
s = df["etc_purps"].fillna(df["main_purps_nm"]).str.replace(r"\s+", "", regex=True).str.lower()
df["cls"] = "cond"
df.loc[s.str.contains(rx(d["semi"])), "cls"] = "semi"
df.loc[s.str.contains(rx(d["noncond"])), "cls"] = "noncond"   # 나중에 덮어써서 우선순위 적용
```

## 알려진 한계

- 문자열 기반이라 층별개요에 주차장이 별도 행으로 기재되지 않은 건물의 주차 공간은 잡히지 않습니다 (표제부 주차면적 필드 미참조).
- 부분 문자열 매칭이므로 `기계`, `전기`, `홀` 같은 짧은 키워드는 과잉 매칭이 있을 수 있습니다. 실제 산출본에서는 건물별 매칭 키워드 컬럼을 함께 제공해 검토 가능하게 했습니다.
- 사전은 전국 층별개요 `etc_purps` 고유 표기(약 17.7만 건)를 대상으로 만들었으며, 새 표기가 나오면 CHANGELOG에 남기고 버전을 올립니다.

## 인용

> BIST Lab, Sungkyunkwan University (2026). *Conditioned-Area Keyword Dictionary for Korean Building Register*, v1.0.0. https://github.com/SKKU-BIST/conditioned-area-keyword-dict

## 라이선스

MIT — 자유롭게 사용·수정·재배포할 수 있고, 출처 표기만 유지하면 됩니다.
