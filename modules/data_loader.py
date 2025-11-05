"""
데이터 로더 모듈
세션에서 데이터 로드 및 전처리
"""

import streamlit as st
import pandas as pd
import numpy as np

def get_annual_learning_data():
    """그룹/멤버사 연간 학습시간 데이터 로드"""
    if 'uploaded_data' in st.session_state and 'annual_learning' in st.session_state.uploaded_data:
        return st.session_state.uploaded_data['annual_learning']
    return None

def get_monthly_learning_data():
    """멤버사 월별 학습시간 데이터 로드"""
    if 'uploaded_data' in st.session_state and 'monthly_learning' in st.session_state.uploaded_data:
        return st.session_state.uploaded_data['monthly_learning']
    return None

def get_individual_data():
    """개인별 학습시간 raw data 로드"""
    if 'uploaded_data' in st.session_state and 'individual_raw' in st.session_state.uploaded_data:
        return st.session_state.uploaded_data['individual_raw']
    return None

def get_popular_cards_data():
    """인기 학습카드 데이터 로드"""
    if 'uploaded_data' in st.session_state and 'popular_cards' in st.session_state.uploaded_data:
        return st.session_state.uploaded_data['popular_cards']
    return None

def get_search_keywords_data():
    """검색어 데이터 로드"""
    if 'uploaded_data' in st.session_state and 'search_keywords' in st.session_state.uploaded_data:
        return st.session_state.uploaded_data['search_keywords']
    return None

def get_area_status_data():
    """주요 영역 인증/이수 현황 데이터 로드"""
    if 'uploaded_data' in st.session_state and 'area_status' in st.session_state.uploaded_data:
        return st.session_state.uploaded_data['area_status']
    return None

def get_individual_full_raw_data():
    """개인별 학습 전체 raw data 로드"""
    if 'uploaded_data' in st.session_state and 'individual_full_raw' in st.session_state.uploaded_data:
        return st.session_state.uploaded_data['individual_full_raw']
    return None

def preprocess_annual_data(df):
    """연간 학습시간 데이터 전처리"""
    if df is None:
        return None
    
    # 연도별 정렬
    if '연도' in df.columns:
        df = df.sort_values('연도')
    
    # 숫자형 컬럼 변환
    numeric_columns = ['학습시간', '전년대비변화율', '상반기_학습시간', '하반기_학습시간']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def preprocess_individual_data(df):
    """개인별 데이터 전처리"""
    if df is None:
        return None
    
    # 숫자형 컬럼 변환
    if '학습시간' in df.columns:
        df['학습시간'] = pd.to_numeric(df['학습시간'], errors='coerce')
    
    # 연도 컬럼 처리 (있는 경우 최신 연도만 사용)
    if '연도' in df.columns:
        # 최신 연도만 사용 (또는 사용자가 선택한 연도)
        if len(df['연도'].unique()) > 1:
            # 기본적으로 최신 연도 사용
            latest_year = df['연도'].max()
            df = df[df['연도'] == latest_year].copy()
    
    # 조직 컬럼명 통일 (조직, 사업부 → 조직)
    if '사업부' in df.columns and '조직' not in df.columns:
        df['조직'] = df['사업부']
    
    # 결측값 처리 (필요시)
    df = df.dropna(subset=['학습시간'])
    
    return df

def get_company_list():
    """멤버사 목록 가져오기"""
    df = get_annual_learning_data()
    if df is not None and '멤버사명' in df.columns:
        return sorted(df['멤버사명'].unique().tolist())
    return []

