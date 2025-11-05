"""
EDA 분석 모듈
조직/직책/개인별 탐색적 데이터 분석
"""

import pandas as pd
import numpy as np
from modules.data_loader import *

def analyze_organization_characteristics(df):
    """조직별 학습 특징 분석 - 상세한 EDA"""
    if df is None or df.empty:
        return None
    
    # 조직 컬럼명 확인 (조직 또는 사업부)
    org_col = None
    for col in ['조직', '사업부', '부서']:
        if col in df.columns:
            org_col = col
            break
    
    if org_col is None:
        return None
    
    # 기본 통계
    org_stats = df.groupby(org_col)['학습시간'].agg([
        'mean', 'median', 'std', 'min', 'max', 'count'
    ]).reset_index()
    org_stats.columns = [org_col, '평균학습시간', '중위수', '표준편차', '최소값', '최대값', '인원수']
    
    # 전체 평균 대비 비교
    overall_mean = df['학습시간'].mean()
    org_stats['평균대비비율'] = (org_stats['평균학습시간'] / overall_mean * 100).round(1)
    
    # 추가 특징 분석
    org_features = []
    for org in org_stats[org_col].unique():
        org_df = df[df[org_col] == org]
        org_data = {
            org_col: org,
            '평균학습시간': org_df['학습시간'].mean(),
            '중위수': org_df['학습시간'].median(),
            '표준편차': org_df['학습시간'].std(),
            '최소값': org_df['학습시간'].min(),
            '최대값': org_df['학습시간'].max(),
            '인원수': len(org_df),
            '평균대비비율': (org_df['학습시간'].mean() / overall_mean * 100).round(1),
            '분산계수': (org_df['학습시간'].std() / org_df['학습시간'].mean() * 100).round(1) if org_df['학습시간'].mean() > 0 else 0
        }
        
        # 학습카드/완료카드 정보 (있는 경우)
        if '학습카드수' in org_df.columns:
            org_data['평균학습카드수'] = org_df['학습카드수'].mean().round(1)
            org_data['평균완료카드수'] = org_df['완료카드수'].mean().round(1) if '완료카드수' in org_df.columns else 0
        
        # Badge 정보 (있는 경우)
        if 'Badge수' in org_df.columns:
            org_data['평균Badge수'] = org_df['Badge수'].mean().round(1)
            org_data['Badge보유인원'] = len(org_df[org_df['Badge수'] > 0])
        
        # 직책 분포 (있는 경우)
        if '직책' in org_df.columns:
            position_dist = org_df['직책'].value_counts().to_dict()
            for pos, count in position_dist.items():
                org_data[f'{pos}_인원수'] = count
                org_data[f'{pos}_비율'] = round(count / len(org_df) * 100, 1)
        
        org_features.append(org_data)
    
    org_enhanced = pd.DataFrame(org_features)
    
    return org_enhanced

def analyze_position_characteristics(df):
    """직책별 학습 특징 분석 - 상세한 EDA (임원, 팀장, 구성원 순서)"""
    if df is None or df.empty or '직책' not in df.columns:
        return None
    
    # 직책 순서 정의 (임원, 팀장, 구성원)
    position_order = ["임원", "팀장", "구성원"]
    
    # 기본 통계
    position_stats = df.groupby('직책')['학습시간'].agg([
        'mean', 'median', 'std', 'count'
    ]).reset_index()
    position_stats.columns = ['직책', '평균학습시간', '중위수', '표준편차', '인원수']
    
    # 전체 평균 대비 비교
    overall_mean = df['학습시간'].mean()
    position_stats['평균대비비율'] = (position_stats['평균학습시간'] / overall_mean * 100).round(1)
    
    # 추가 특징 분석
    position_features = []
    for pos in position_order:
        if pos not in df['직책'].unique():
            continue
            
        pos_df = df[df['직책'] == pos]
        pos_data = {
            '직책': pos,
            '평균학습시간': pos_df['학습시간'].mean(),
            '중위수': pos_df['학습시간'].median(),
            '표준편차': pos_df['학습시간'].std(),
            '최소값': pos_df['학습시간'].min(),
            '최대값': pos_df['학습시간'].max(),
            '인원수': len(pos_df),
            '평균대비비율': (pos_df['학습시간'].mean() / overall_mean * 100).round(1),
            '분산계수': (pos_df['학습시간'].std() / pos_df['학습시간'].mean() * 100).round(1) if pos_df['학습시간'].mean() > 0 else 0
        }
        
        # 학습카드/완료카드 정보 (있는 경우)
        if '학습카드수' in pos_df.columns:
            pos_data['평균학습카드수'] = pos_df['학습카드수'].mean().round(1)
            pos_data['평균완료카드수'] = pos_df['완료카드수'].mean().round(1) if '완료카드수' in pos_df.columns else 0
            pos_data['평균완료률'] = (pos_data['평균완료카드수'] / pos_data['평균학습카드수'] * 100).round(1) if pos_data['평균학습카드수'] > 0 else 0
        
        # Badge 정보 (있는 경우)
        if 'Badge수' in pos_df.columns:
            pos_data['평균Badge수'] = pos_df['Badge수'].mean().round(1)
            pos_data['Badge보유인원'] = len(pos_df[pos_df['Badge수'] > 0])
            pos_data['Badge보유율'] = round(pos_data['Badge보유인원'] / len(pos_df) * 100, 1) if len(pos_df) > 0 else 0
        
        # 연령대 분포 (있는 경우)
        if '연령대' in pos_df.columns:
            age_dist = pos_df['연령대'].value_counts().to_dict()
            pos_data['주요연령대'] = max(age_dist.items(), key=lambda x: x[1])[0] if age_dist else '-'
        
        # 성별 분포 (있는 경우)
        if '성별' in pos_df.columns:
            gender_dist = pos_df['성별'].value_counts().to_dict()
            pos_data['남성비율'] = round(gender_dist.get('남성', 0) / len(pos_df) * 100, 1) if len(pos_df) > 0 else 0
            pos_data['여성비율'] = round(gender_dist.get('여성', 0) / len(pos_df) * 100, 1) if len(pos_df) > 0 else 0
        
        # 직무 분포 (있는 경우)
        if '직무' in pos_df.columns:
            job_dist = pos_df['직무'].value_counts().to_dict()
            pos_data['주요직무'] = max(job_dist.items(), key=lambda x: x[1])[0] if job_dist else '-'
        
        position_features.append(pos_data)
    
    # 정의된 순서대로 정렬
    position_enhanced = pd.DataFrame(position_features)
    
    return position_enhanced

def analyze_individual_characteristics(df):
    """개인별 학습 특징 분석"""
    if df is None or df.empty or '학습시간' not in df.columns:
        return None
    
    stats = {
        '총인원수': len(df),
        '평균학습시간': df['학습시간'].mean(),
        '중위수학습시간': df['학습시간'].median(),
        '표준편차': df['학습시간'].std(),
        '최소값': df['학습시간'].min(),
        '최대값': df['학습시간'].max(),
        '1사분위수': df['학습시간'].quantile(0.25),
        '3사분위수': df['학습시간'].quantile(0.75),
        '분산계수': (df['학습시간'].std() / df['학습시간'].mean() * 100) if df['학습시간'].mean() > 0 else 0
    }
    
    # 저학습자/고학습자 구분
    q1 = stats['1사분위수']
    q3 = stats['3사분위수']
    
    low_learners = df[df['학습시간'] < q1].copy()
    high_learners = df[df['학습시간'] > q3].copy()
    
    stats['저학습자수'] = len(low_learners)
    stats['고학습자수'] = len(high_learners)
    stats['저학습자비율'] = round(len(low_learners) / len(df) * 100, 1) if len(df) > 0 else 0
    stats['고학습자비율'] = round(len(high_learners) / len(df) * 100, 1) if len(df) > 0 else 0
    
    if len(low_learners) > 0:
        stats['저학습자평균'] = low_learners['학습시간'].mean()
    
    if len(high_learners) > 0:
        stats['고학습자평균'] = high_learners['학습시간'].mean()
    
    return stats, low_learners, high_learners

def format_stats_for_gemini(stats_dict):
    """통계 데이터를 Gemini 프롬프트용 텍스트로 변환"""
    text = "통계 분석 결과:\n\n"
    
    for key, value in stats_dict.items():
        if isinstance(value, (int, float)):
            if isinstance(value, float):
                text += f"- {key}: {value:.2f}\n"
            else:
                text += f"- {key}: {value}\n"
        elif isinstance(value, pd.DataFrame):
            text += f"\n{key}:\n{value.to_string()}\n\n"
    
    return text

def get_enhanced_eda_summary(stats_df, analysis_type='조직별'):
    """향상된 EDA 요약 정보 생성 (Gemini 프롬프트용)"""
    if stats_df is None or stats_df.empty:
        return ""
    
    summary = f"\n{analysis_type} 학습 특징 분석 데이터:\n\n"
    summary += stats_df.to_string(index=False)
    
    # 추가 분석 정보
    if analysis_type == '조직별':
        summary += "\n\n각 조직의 특징:\n"
        for _, row in stats_df.iterrows():
            org_name = row.iloc[0]  # 첫 번째 컬럼이 조직명
            avg_time = row.get('평균학습시간', 0)
            members = row.get('인원수', 0)
            summary += f"- {org_name}: 평균 학습시간 {avg_time:.1f}시간, 인원 {members}명\n"
    
    elif analysis_type == '직책별':
        summary += "\n\n각 직책의 특징:\n"
        for _, row in stats_df.iterrows():
            position = row.get('직책', '-')
            avg_time = row.get('평균학습시간', 0)
            members = row.get('인원수', 0)
            badge_rate = row.get('Badge보유율', 0) if 'Badge보유율' in row else 0
            summary += f"- {position}: 평균 학습시간 {avg_time:.1f}시간, 인원 {members}명, Badge 보유율 {badge_rate:.1f}%\n"
    
    return summary
