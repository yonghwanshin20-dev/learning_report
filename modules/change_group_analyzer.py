"""
변화군 분석 모듈
학습시간 변화군 분류 및 분석 (22-25년도 지원)
"""

import pandas as pd
import numpy as np
import yaml
import os

def load_thresholds():
    """변화군 분류 임계값 로드"""
    config_path = 'config.yaml'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            return config.get('change_group_thresholds', {
                'low_learning_threshold': 0.5,
                'high_learning_threshold': 1.5,
                'increase_threshold': 0.1,
                'decrease_threshold': -0.1
            })
    return {
        'low_learning_threshold': 0.5,
        'high_learning_threshold': 1.5,
        'increase_threshold': 0.1,
        'decrease_threshold': -0.1
    }

def classify_change_groups(df):
    """
    학습시간 변화군 분류 (22-25년도 지원)
    - 지속 저학습군: 모든 연도 낮음
    - 지속 고학습군: 모든 연도 높음
    - 상승군: 연도별 증가 추세
    - 하락군: 연도별 감소 추세
    - 불규칙군: 일관된 패턴 없음
    """
    if df is None or df.empty:
        return {}
    
    thresholds = load_thresholds()
    
    # 연도 컬럼이 있는지 확인
    if '연도' not in df.columns or '학습시간' not in df.columns:
        return {}
    
    # 개인ID 확인
    person_col = '개인ID' if '개인ID' in df.columns else None
    if person_col is None:
        return {}
    
    # 각 개인별로 연도별 데이터 피벗
    if '연도' in df.columns and '학습시간' in df.columns:
        # 개인별 연도별 학습시간 피벗
        pivot_df = df.pivot_table(
            index=person_col,
            columns='연도',
            values='학습시간',
            aggfunc='sum'
        ).fillna(0)
        
        # 연도 컬럼명 정규화
        year_cols = [col for col in pivot_df.columns if isinstance(col, (int, np.integer))]
        if not year_cols:
            return {}
        
        # 최근 2년 (2024, 2025) 또는 가능한 연도 선택
        available_years = sorted([y for y in year_cols if y >= 2022])
        
        if len(available_years) < 2:
            return {}
        
        # 2024, 2025 연도 확인 (없으면 최근 2년 사용)
        if 2024 in available_years and 2025 in available_years:
            col_2024 = 2024
            col_2025 = 2025
        else:
            col_2024 = available_years[-2]
            col_2025 = available_years[-1]
        
        # 전체 평균 계산
        mean_2024 = pivot_df[col_2024].mean()
        mean_2025 = pivot_df[col_2025].mean()
        overall_mean = (mean_2024 + mean_2025) / 2
        
        # 변화율 계산
        pivot_df['변화율'] = ((pivot_df[col_2025] - pivot_df[col_2024]) / (pivot_df[col_2024] + 1) * 100).fillna(0)
        pivot_df['24년학습시간'] = pivot_df[col_2024]
        pivot_df['25년학습시간'] = pivot_df[col_2025]
        pivot_df['개인ID'] = pivot_df.index
        
        # 변화군 분류
        change_groups = {
            '지속 저학습군': [],
            '지속 고학습군': [],
            '상승군': [],
            '하락군': [],
            '불규칙군': []
        }
        
        for person_id in pivot_df.index:
            time_2024 = pivot_df.loc[person_id, col_2024]
            time_2025 = pivot_df.loc[person_id, col_2025]
            change_rate = pivot_df.loc[person_id, '변화율']
            
            # 저학습/고학습 기준
            is_low_2024 = time_2024 < overall_mean * thresholds['low_learning_threshold']
            is_low_2025 = time_2025 < overall_mean * thresholds['low_learning_threshold']
            is_high_2024 = time_2024 > overall_mean * thresholds['high_learning_threshold']
            is_high_2025 = time_2025 > overall_mean * thresholds['high_learning_threshold']
            
            # 장기 패턴 확인 (가능한 경우)
            is_consistently_low = is_low_2024 and is_low_2025
            is_consistently_high = is_high_2024 and is_high_2025
            
            # 변화군 분류
            if is_consistently_low:
                change_groups['지속 저학습군'].append(person_id)
            elif is_consistently_high:
                change_groups['지속 고학습군'].append(person_id)
            elif change_rate >= thresholds['increase_threshold'] * 100:
                change_groups['상승군'].append(person_id)
            elif change_rate <= thresholds['decrease_threshold'] * 100:
                change_groups['하락군'].append(person_id)
            else:
                change_groups['불규칙군'].append(person_id)
        
        return change_groups
    
    return {}

def get_change_group_statistics(df, change_groups):
    """변화군별 통계 정보"""
    if df is None or df.empty or not change_groups:
        return None
    
    stats = []
    
    # 연도별 데이터 준비
    if '연도' in df.columns and '학습시간' in df.columns:
        pivot_df = df.pivot_table(
            index='개인ID',
            columns='연도',
            values='학습시간',
            aggfunc='sum'
        ).fillna(0)
    else:
        return None
    
    available_years = sorted([y for y in pivot_df.columns if isinstance(y, (int, np.integer)) and y >= 2022])
    
    for group_name, member_ids in change_groups.items():
        if not member_ids:
            continue
        
        # 해당 변화군의 데이터
        group_df = pivot_df[pivot_df.index.isin(member_ids)]
        
        if group_df.empty:
            continue
        
        group_stats = {
            '변화군': group_name,
            '인원수': len(member_ids),
        }
        
        # 각 연도별 평균 학습시간
        for year in available_years:
            if year in group_df.columns:
                group_stats[f'{year}년평균학습시간'] = round(group_df[year].mean(), 1)
        
        # 최근 2년 변화율 계산
        if 2024 in available_years and 2025 in available_years:
            time_2024 = group_df[2024].mean() if 2024 in group_df.columns else 0
            time_2025 = group_df[2025].mean() if 2025 in group_df.columns else 0
            if time_2024 > 0:
                change_rate = ((time_2025 - time_2024) / time_2024 * 100)
                group_stats['평균변화율(%)'] = round(change_rate, 1)
        
        stats.append(group_stats)
    
    return pd.DataFrame(stats)
