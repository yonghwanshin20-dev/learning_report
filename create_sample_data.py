"""
샘플 데이터 생성 스크립트
모든 파일 타입에 대한 샘플 데이터를 생성합니다.
"""

import sys
import io

# Windows 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime
import os

# 샘플 데이터 저장 디렉토리
SAMPLE_DIR = "sample_data"
os.makedirs(SAMPLE_DIR, exist_ok=True)

# 새로운 멤버사 리스트 (17개)
COMPANIES = [
    "SK Inc.", "SK하이닉스", "SK텔레콤", "SK이노베이션", "SK브로드밴드",
    "SK네트웍스", "SKC", "SK E&S", "SK온", "SK AX",
    "SK케미칼", "SK바이오팜", "SK디스커버리", "SK머티리얼즈", "SK실트론",
    "SK에코플랜트", "SK가스", "SK스퀘어"
]

# Demo 정보 구성 요소
BUSINESS_UNITS = ["본사", "사업부1", "사업부2", "사업부3", "사업부4", "사업부5", "R&D센터", "글로벌사업부"]
POSITIONS = ["임원", "팀장", "구성원"]
AGE_GROUPS = ["20대", "30대", "40대", "50대", "60대"]
GENDERS = ["남성", "여성"]
JOBS = ["경영", "영업", "마케팅", "R&D", "생산", "품질", "인사", "재무", "IT", "기획"]

# 회사별 평균 학습시간 가중치(인당) - 회사 간 차등 부여
COMPANY_FACTORS = {
    "SK Inc.": 1.05,
    "SK하이닉스": 1.10,
    "SK텔레콤": 1.00,
    "SK이노베이션": 0.95,
    "SK브로드밴드": 0.90,
    "SK네트웍스": 0.92,
    "SKC": 0.98,
    "SK E&S": 1.08,
    "SK온": 1.12,
    "SK AX": 0.97,
    "SK케미칼": 0.93,
    "SK바이오팜": 1.15,
    "SK디스커버리": 0.96,
    "SK머티리얼즈": 1.03,
    "SK실트론": 1.06,
    "SK에코플랜트": 0.88,
    "SK가스": 0.91,
    "SK스퀘어": 1.02
}

# 총 학습자 수: 10,000명
TOTAL_LEARNERS = 10000

# 하이닉스 비율: 약 30% (3000명)
HYNIX_RATIO = 0.3
HYNIX_LEARNERS = int(TOTAL_LEARNERS * HYNIX_RATIO)
OTHER_LEARNERS = TOTAL_LEARNERS - HYNIX_LEARNERS

# 하이닉스와 다른 회사 간 학습자 수 분배
COMPANY_LEARNERS = {}
COMPANY_LEARNERS['SK하이닉스'] = HYNIX_LEARNERS
other_companies = [c for c in COMPANIES if c != 'SK하이닉스']
learners_per_other = OTHER_LEARNERS // len(other_companies)
for company in other_companies:
    COMPANY_LEARNERS[company] = learners_per_other

# 나머지 인원을 첫 번째 회사에 추가
remaining = OTHER_LEARNERS - (learners_per_other * len(other_companies))
if remaining > 0:
    COMPANY_LEARNERS[other_companies[0]] += remaining

print("샘플 데이터 생성 시작...")
print(f"총 학습자 수: {TOTAL_LEARNERS:,}명")
print(f"SK하이닉스: {COMPANY_LEARNERS['SK하이닉스']:,}명 ({HYNIX_RATIO*100:.1f}%)")

# 개인 ID 생성 (10,000명)
person_counter = 1
PERSON_IDS = []

print(f"\n개인 ID 생성 중...")
print(f"예상 학습자 수 분배:")
for company in COMPANIES:
    num_learners = COMPANY_LEARNERS.get(company, 0)
    print(f"  - {company}: {num_learners:,}명")

# 실제로 10,000명 생성 확인
for company in COMPANIES:
    num_learners = COMPANY_LEARNERS.get(company, 0)
    if num_learners > 0:
        for i in range(num_learners):
            PERSON_IDS.append({
                '개인ID': f"EMP{person_counter:05d}",
                '멤버사명': company
            })
            person_counter += 1

# 실제 생성된 개인 ID 수 확인
actual_total = len(PERSON_IDS)
print(f"\n✓ 개인 ID 생성 완료: 총 {actual_total:,}명")
print(f"   - 각 회사별 인원 수 확인:")
total_check = 0
for company in COMPANIES:
    company_count = len([p for p in PERSON_IDS if p['멤버사명'] == company])
    total_check += company_count
    if company_count > 0:
        print(f"     {company}: {company_count:,}명")

if actual_total != TOTAL_LEARNERS:
    print(f"\n⚠ 경고: 예상 인원({TOTAL_LEARNERS:,}명)과 실제 생성 인원({actual_total:,}명)이 다릅니다!")
    print(f"   검증 합계: {total_check:,}명")
else:
    print(f"\n✓ 정확히 {TOTAL_LEARNERS:,}명이 생성되었습니다!")

person_df = pd.DataFrame(PERSON_IDS)

# 1. 연간 학습시간 (22-25년) - 컬럼명/단위 변경
print("\n1. 연간 학습시간 생성 중...")
annual_data = []
for company in COMPANIES:
    base_time_hours = np.random.randint(50000, 500000)  # 시간 단위
    for year in [2022, 2023, 2024, 2025]:
        growth = (year - 2022) * 0.1
        hours = int(base_time_hours * (1 + growth) * np.random.uniform(0.9, 1.1))
        prev_hours = annual_data[-1]['학습시간(분)'] / 60 if year > 2022 else hours
        change_rate = ((hours - prev_hours) / prev_hours * 100) if prev_hours > 0 else 0

        annual_data.append({
            'company_name_kor': company,
            'base_year': year,
            '학습시간(분)': hours * 60,  # 분 단위
            '전년대비변화율': round(change_rate, 2) if year > 2022 else 0,
            '상반기학습시간(분)': int(hours * np.random.uniform(0.45, 0.55)) * 60,
            '하반기학습시간(분)': int(hours * np.random.uniform(0.45, 0.55)) * 60
        })

df_annual = pd.DataFrame(annual_data)
df_annual.to_excel(f"{SAMPLE_DIR}/1. 연간 학습시간.xlsx", index=False)
print(f"   ✓ {len(df_annual)}개 레코드 생성")

# 2. 월별 학습시간
print("\n2. 월별 학습시간 생성 중...")
monthly_data = []
for company in COMPANIES:
    for year in [2022, 2023, 2024, 2025]:
        base_monthly = np.random.randint(3000, 20000)
        for month in range(1, 13):
            # 계절성 반영 (상반기/하반기 패턴)
            seasonal_factor = 1.1 if month <= 6 else 0.9
            hours = int(base_monthly * seasonal_factor * np.random.uniform(0.8, 1.2))
            monthly_data.append({
                'company_name_kor': company,
                'base_year': year,
                'base_yearmonth': year * 100 + month,
                '학습시간(분)': hours * 60
            })

df_monthly = pd.DataFrame(monthly_data)
df_monthly.to_excel(f"{SAMPLE_DIR}/2. 월별 학습시간.xlsx", index=False)
print(f"   ✓ {len(df_monthly)}개 레코드 생성")

# 3. 카테고리별 학습시간
print("\n3. 카테고리별 학습시간 생성 중...")
categories = [
    "경영철학", "AI/DT", "공통직무역량", "리더십", "디지털 트랜스포메이션",
    "데이터 분석", "프로젝트 관리", "협상 및 커뮤니케이션", "글로벌 비즈니스", "혁신경영"
]
category_data = []
for category in categories:
    hours = np.random.randint(10000, 100000)
    learners = np.random.randint(500, 3000)
    category_data.append({
        'category_name_kor': category,
        '학습시간(분)': hours * 60,
        '학습인원': learners,
        '평균학습시간': round(hours / learners, 2) if learners > 0 else 0
    })

df_category = pd.DataFrame(category_data)
df_category.to_excel(f"{SAMPLE_DIR}/3. 카테고리별 학습시간.xlsx", index=False)
print(f"   ✓ {len(df_category)}개 레코드 생성")

# 4. 인기학습카드
print("\n4. 인기학습카드 생성 중...")
popular_cards = [
    "디지털 혁신 전략", "데이터 기반 의사결정", "Agile 프로젝트 관리",
    "AI 활용 비즈니스 모델", "고객 경험 혁신", "디지털 마케팅 전략",
    "클라우드 마이그레이션", "사이버 보안 기초", "빅데이터 분석 기초",
    "디자인 씽킹", "고객 중심 서비스 디자인", "데이터 시각화",
    "머신러닝 기초", "블록체인과 비즈니스", "클라우드 아키텍처"
]
card_data = []
for i, card in enumerate(popular_cards):
    learners = np.random.randint(200, 2000)
    avg_time = np.random.uniform(5, 25)
    completion_rate = np.random.uniform(65, 95)
    card_data.append({
        'card_name_kor': card,
        '학습인원': learners,
        '평균학습시간': round(avg_time, 1),
        '완료률': round(completion_rate, 1)
    })

df_cards = pd.DataFrame(card_data)
df_cards = df_cards.rename(columns={'학습인원': '학습자수'})
df_cards = df_cards.sort_values('학습자수', ascending=False)
df_cards.to_excel(f"{SAMPLE_DIR}/4. 인기학습카드.xlsx", index=False)
print(f"   ✓ {len(df_cards)}개 레코드 생성")

# 5. 검색어
print("\n5. 검색어 생성 중...")
keywords = [
    "AI", "데이터 분석", "프로젝트 관리", "리더십", "디지털 트랜스포메이션",
    "마케팅", "고객 경험", "비즈니스 모델", "혁신", "데이터 사이언스",
    "머신러닝", "클라우드", "블록체인", "사이버 보안", "디지털 마케팅"
]
search_data = []
for keyword in keywords:
    for year in [2022, 2023, 2024, 2025]:
        # 연도별 증가 추세
        growth_factor = 1 + (year - 2022) * 0.15
        search_count = int(np.random.randint(500, 5000) * growth_factor)
        search_data.append({
            'key_word': keyword,
            'base_year': year,
            'count': search_count
        })

df_search = pd.DataFrame(search_data)
df_search.to_excel(f"{SAMPLE_DIR}/5. 검색어.xlsx", index=False)
print(f"   ✓ {len(df_search)}개 레코드 생성")

# 6. 개인별 학습시간 raw (연도 포함)
print(f"\n6. 개인별 학습시간 raw 생성 중... (총 {len(PERSON_IDS):,}명)")
individual_data = []

# 각 개인에게 Demo 정보 할당
np.random.seed(42)  # 재현 가능한 결과를 위해

# 진행 상황 표시를 위한 카운터
processed_count = 0
total_persons = len(PERSON_IDS)

for person_info in PERSON_IDS:
    processed_count += 1
    if processed_count % 1000 == 0 or processed_count == total_persons:
        print(f"   진행: {processed_count:,}/{total_persons:,}명 ({processed_count*100//total_persons}%)")
    person_id = person_info['개인ID']
    company = person_info['멤버사명']
    
    # Demo 정보 생성
    사업부 = np.random.choice(BUSINESS_UNITS)
    직책 = np.random.choice(POSITIONS, p=[0.05, 0.15, 0.8])  # 구성원 비율 높음
    연령대 = np.random.choice(AGE_GROUPS, p=[0.15, 0.35, 0.30, 0.15, 0.05])
    성별 = np.random.choice(GENDERS)
    직무 = np.random.choice(JOBS)
    
    # 연도별 학습시간 생성 (22-25년)
    for year in [2022, 2023, 2024, 2025]:
        # 직책별 기본 학습시간 차이 (평균 30~50시간 목표)
        if 직책 == "임원":
            base_time = np.random.randint(60, 120)
        elif 직책 == "팀장":
            base_time = np.random.randint(45, 90)
        else:
            base_time = np.random.randint(25, 60)

        # 조직(사업부) 가중치로 차등 부여
        org_factor_map = {
            "본사": 1.1,
            "사업부1": 0.9,
            "사업부2": 1.0,
            "사업부3": 1.2,
            "사업부4": 0.8,
            "사업부5": 1.05,
            "R&D센터": 1.3,
            "글로벌사업부": 1.15
        }
        org_factor = org_factor_map.get(사업부, 1.0)
        
        # 연도별 증가 추세
        year_factor = 1 + (year - 2022) * 0.1
        comp_factor = COMPANY_FACTORS.get(company, 1.0)
        learning_time = int(base_time * org_factor * comp_factor * year_factor * np.random.uniform(0.7, 1.3))
        
        individual_data.append({
            'user_id': person_id,
            '이름': f"직원{int(person_id[-5:])}",
            'company_name_kor': company,
            'base_year': year,
            '사업부': 사업부,
            '직책': 직책,
            '연령대': 연령대,
            '성별': 성별,
            '직무': 직무,
            '학습시간(분)': learning_time * 60,
            '학습카드수': np.random.randint(5, 50),
            '완료카드수': np.random.randint(3, 40),
            'Badge수': np.random.randint(0, 10)
        })

df_individual = pd.DataFrame(individual_data)
df_individual.to_excel(f"{SAMPLE_DIR}/6. 개인별 학습시간 raw.xlsx", index=False)
print(f"   ✓ {len(df_individual):,}개 레코드 생성")

# 7. 카드별 학습시간 raw
print("\n7. 카드별 학습시간 raw 생성 중...")
card_raw_data = []
for i in range(1, 101):  # 100개 학습카드
    card_raw_data.append({
        '학습카드ID': f"CARD{i:03d}",
        'card_name_kor': f"학습카드 {i}",
        'category_name_kor': np.random.choice(categories),
        '생성일': datetime(2022 + np.random.randint(0, 4), np.random.randint(1, 13), np.random.randint(1, 29)),
        '이수인원': np.random.randint(50, 500),
        '현재학습인원': np.random.randint(20, 200),
        '평균학습시간': round(np.random.uniform(3, 20), 1)
    })

df_card_raw = pd.DataFrame(card_raw_data)
df_card_raw.to_excel(f"{SAMPLE_DIR}/7. 카드별 학습시간 raw.xlsx", index=False)
print(f"   ✓ {len(df_card_raw)}개 레코드 생성")

# 8. Badge별 학습시간 raw
print("\n8. Badge별 학습시간 raw 생성 중...")
badge_names = [
    "디지털 리더", "데이터 분석가", "AI 전문가", "프로젝트 매니저",
    "혁신가", "커뮤니케이터", "글로벌 비즈니스 전문가", "전략가",
    "디지털 마케터", "클라우드 아키텍트"
]
badge_data = []
for i, badge_name in enumerate(badge_names):
    badge_data.append({
        'BadgeID': f"BADGE{i+1:02d}",
        '뱃지명': badge_name,
        '설명': f"{badge_name} 배지",
        '취득인원': np.random.randint(100, 1000),
        '도전중인원': np.random.randint(50, 500),
        '필요학습시간': np.random.randint(20, 100)
    })

df_badge = pd.DataFrame(badge_data)
df_badge.to_excel(f"{SAMPLE_DIR}/8. Badge별 학습시간 raw.xlsx", index=False)
print(f"   ✓ {len(df_badge)}개 레코드 생성")

# 9. 개인별 학습 전체 raw (22-25년도)
print(f"\n9. 개인별 학습 전체 raw 생성 중... (총 {len(PERSON_IDS):,}명)")
individual_full_data = []

# 각 개인에 대해 22-25년도 데이터 생성
# 진행 상황 표시를 위한 카운터
processed_count = 0
total_persons = len(PERSON_IDS)

for person_info in PERSON_IDS:
    processed_count += 1
    if processed_count % 1000 == 0 or processed_count == total_persons:
        print(f"   진행: {processed_count:,}/{total_persons:,}명 ({processed_count*100//total_persons}%)")
    person_id = person_info['개인ID']
    company = person_info['멤버사명']
    
    # 개인의 연속된 학습 패턴 생성 (시간 단위 내부 계산)
    base_2022_time_hours = int(np.random.randint(20, 150) * COMPANY_FACTORS.get(company, 1.0))
    last_time_hours = base_2022_time_hours
    
    for year_idx, year in enumerate([2022, 2023, 2024, 2025]):
        if year_idx > 0:
            # 변화율 (-30% ~ +50%)
            change_rate = np.random.uniform(-0.3, 0.5)
            last_time_hours = max(0, int(last_time_hours * (1 + change_rate)))
        
        individual_full_data.append({
            'user_id': person_id,
            'company_name_kor': company,
            'base_year': year,
            '학습시간(분)': last_time_hours * 60,
            '학습카드수': np.random.randint(5, 50),
            '완료카드수': np.random.randint(3, 40),
            'Badge수': np.random.randint(0, 10)
        })

df_individual_full = pd.DataFrame(individual_full_data)
df_individual_full.to_excel(f"{SAMPLE_DIR}/9. 개인별 학습 전체 raw.xlsx", index=False)
print(f"   ✓ {len(df_individual_full):,}개 레코드 생성")

print(f"\n{'='*50}")
print(f"[OK] 샘플 데이터 생성 완료! ({SAMPLE_DIR} 폴더에 저장됨)")
print(f"{'='*50}")
print(f"\n생성된 파일:")
for i, file in enumerate(sorted(os.listdir(SAMPLE_DIR)), 1):
    file_path = os.path.join(SAMPLE_DIR, file)
    if os.path.isfile(file_path):
        file_size = os.path.getsize(file_path)
        print(f"  {i:2d}. {file} ({file_size:,} bytes)")

print(f"\n{'='*50}")
print(f"요약:")
print(f"{'='*50}")
print(f"  - 총 학습자 수: {len(PERSON_IDS):,}명 (목표: {TOTAL_LEARNERS:,}명)")
if len(PERSON_IDS) == TOTAL_LEARNERS:
    print(f"  ✓ 목표 인원 수 정확히 생성됨!")
else:
    print(f"  ⚠ 경고: 목표와 실제 생성 인원이 다릅니다!")
print(f"  - SK하이닉스: {COMPANY_LEARNERS['SK하이닉스']:,}명 ({HYNIX_RATIO*100:.1f}%)")
print(f"  - 연도 범위: 2022-2025년")
print(f"  - 개인별 학습시간 raw: {len(df_individual):,}개 레코드 (예상: {len(PERSON_IDS)*4:,}개)")
print(f"  - 개인별 학습 전체 raw: {len(df_individual_full):,}개 레코드 (예상: {len(PERSON_IDS)*4:,}개)")
