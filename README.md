# 냉난방(공조)면적 산출용 키워드 사전
### Conditioned-Area Keyword Dictionary for Korean Building Register (건축물대장 층별개요)

건축물대장 **층별개요**의 층기타용도(`etc_purps`)와 층주용도(`main_purps_nm`) 문자열을 기준으로,
각 층(또는 층 내 공간)을 **비공조 / 준공조 / 공조**로 분류하기 위한 키워드 사전과 참조 구현입니다.
성균관대학교 BIST Lab이 전국 6,929,716동의 냉난방면적(`cond_area`)을 산출할 때 실제로 적용한 사전과 동일한 버전입니다.

| 항목 | 내용 |
|---|---|
| 사전 버전 | v1.1.0 (키워드 확정일 2026-06-08, 공간 이름 사전 추가 2026-09-11) |
| 키워드 수 | 비공조 152 · 준공조 34 · (주차계열 11, 비공조의 부분집합) |
| 매칭 방식 | 공백 제거·소문자화 후 **부분 문자열(substring)** 매칭 |
| 우선순위 | 비공조 > 준공조 > 그 외 전부 공조 |

## 파일

| 파일 | 설명 |
|---|---|
| `keyword_dictionary.csv` | 배포용 표 (no, keyword, class, is_parking, match_type, priority). UTF-8(BOM) 인코딩이라 엑셀에서 바로 열립니다 |
| `keyword_dictionary.json` | 프로그램용. `noncond`, `semi`, `parking` 키워드 목록과 메타 정보 |
| `classify.py` | 참조 구현 (문자열 분류, 행 분해, 건물 단위 집계). 외부 의존성 없음, Python 3.8 이상 |
| `space_name_lexicon.csv` | **공간 이름 사전** — 전국 층별개요에서 실제로 관측되어 비공조·준공조로 판정된 공간 이름 전체 (비공조 177,746 · 준공조 67,961). 이름별 매칭 키워드, 출현 행수, 면적 합 수록 |
| `space_name_lexicon_cond.csv` | 공조로 판정된 공간 이름 199,269건 (참고용, 같은 형식) |
| `CHANGELOG.md` | 버전 이력 |

## 분류 규칙

1. 층별개요 각 행의 `etc_purps`를 기준으로 하며, 비어 있으면 `main_purps_nm`을 사용합니다.
2. `"용도명(123.4㎡)"` 형태의 괄호 면적 표기가 있으면 `/ , · ; |` 구분자로 토큰을 나누어 토큰별로 판정합니다. 없으면 행 전체를 하나의 토큰으로 보고 행 면적(`area`)을 사용합니다.
3. 토큰의 공백을 제거하고 소문자로 바꾼 뒤 다음 순서로 판정합니다.
   - **비공조 키워드**가 하나라도 포함되면 `noncond` (주차, 계단, 승강기, 기계실, 화장실, 탱크, 축사, 옥외 등)
   - 그렇지 않고 **준공조 키워드**가 포함되면 `semi` (창고, 공장, 냉장, 발코니, 현관, 홀 등)
   - 둘 다 해당하지 않으면 `cond` (주거, 업무, 상업, 교육, 의료, 숙박 등 나머지 전부)
4. 주차 키워드(주차, 차고, 램프, 필로티 등)가 포함되면 `is_parking = Y`로 표시합니다. 이 값은 시설면적(전체 − 주차)과 용면적(지상 비주차) 산출에 사용합니다.

건물 단위로는 다음과 같이 집계합니다.

```
cond_area    = Σ cond 토큰 면적          ← 냉난방(공조)면적
semi_area    = Σ semi 토큰 면적          ← 별도 집계 (필요 시 cond에 합산)
noncond_area = Σ noncond 토큰 면적
```

준공조는 냉난방을 부분적·간헐적으로만 하거나(창고, 공장 등) 산업용 냉장처럼 판단이 갈리는 공간이므로, 공조면적에 합산하지 않고 별도로 집계합니다. 보수적으로 보려면 `cond_area`만, 넓게 보려면 `cond_area + semi_area`를 사용하면 됩니다.

## 공간 이름 사전 (space_name_lexicon.csv)

키워드 186개가 실제 데이터에서 어떤 이름에 걸렸는지 확인할 수 있도록, 전국 층별개요 20,670,074행을 토큰 단위로 분해해 관측된 고유 이름 444,976건 전부를 분류별로 정리했습니다. 키워드 사전을 검토하거나, 특정 이름이 어떻게 분류되는지 찾아볼 때 사용합니다.

| 컬럼 | 내용 |
|---|---|
| `space_name` | 공백 제거·소문자화된 공간 이름 (괄호 면적 표기는 제거) |
| `class` | 비공조 / 준공조 / 공조 |
| `is_parking` | 주차 키워드 매칭 여부 |
| `matched_keywords` | 판정에 걸린 키워드 전부 (`\|` 구분) |
| `n_rows` | 전국 층별개요 출현 행수 |
| `area_sum_m2` | 해당 이름 행의 면적 합 (㎡) |

예를 들어 `단독주택(창고)`는 `창고` 키워드 때문에 준공조로, `계단실(연면적제외)`는 `계단`·`연면적제외` 키워드로 비공조로 분류됩니다. 부분 문자열 매칭의 한계가 드러나는 이름을 이 파일에서 찾아 사전 개선에 반영할 수 있습니다.

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

pandas에서 직접 적용하려면 `keyword_dictionary.json`의 키워드 목록을 정규식으로 합쳐 `str.contains`로 검사하면 같은 결과를 얻을 수 있습니다.

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

- 문자열 기반 판정이므로, 층별개요에 주차장이 별도 행으로 기재되지 않은 건물의 주차 공간은 검출되지 않습니다 (표제부의 주차면적 필드는 참조하지 않습니다).
- 부분 문자열 매칭이므로 `기계`, `전기`, `홀`처럼 짧은 키워드는 의도하지 않은 표기까지 매칭될 수 있습니다. 실제 산출본에는 건물별로 매칭된 키워드 컬럼을 함께 수록해 검토할 수 있도록 했습니다.
- 사전은 전국 층별개요 `etc_purps`의 고유 표기 약 17.7만 건을 검토해 구축했으며, 새로운 표기가 확인되면 CHANGELOG에 기록하고 버전을 갱신합니다.

## 인용

> BIST Lab, Sungkyunkwan University (2026). *Conditioned-Area Keyword Dictionary for Korean Building Register*, v1.1.0. https://github.com/SKKU-BIST/conditioned-area-keyword-dict

## 라이선스

MIT 라이선스입니다. 저작권 표시를 유지하는 조건으로 자유롭게 사용·수정·재배포할 수 있습니다.
