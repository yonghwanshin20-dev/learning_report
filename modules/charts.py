"""
차트 생성 모듈
각 분석 항목별 차트 생성
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from modules.data_loader import *

def create_annual_trend_chart(df, selected_company=None):
    """최근 3개년 학습시간 추이 차트"""
    if df is None or df.empty:
        return None
    
    # 데이터 필터링
    plot_df = df.copy()
    if selected_company:
        plot_df = plot_df[plot_df['멤버사명'] == selected_company]
    
    # 연도별 집계
    if '연도' in plot_df.columns and '학습시간' in plot_df.columns:
        yearly_data = plot_df.groupby('연도')['학습시간'].sum().reset_index()
        
        fig = px.line(
            yearly_data,
            x='연도',
            y='학습시간',
            title='최근 3개년 학습시간 추이',
            markers=True,
            labels={'학습시간': '학습시간 (시간)', '연도': '연도'}
        )
        
        fig.update_layout(
            xaxis=dict(tickmode='linear'),
            hovermode='x unified'
        )
        
        return fig
    return None

def create_matrix_chart(df):
    """그룹/각 사별 학습시간 Matrix 차트"""
    if df is None or df.empty:
        return None
    
    # 전년 대비 변화율과 올해 학습시간이 필요한 경우
    # 데이터 구조에 따라 조정 필요
    if '전년대비변화율' in df.columns and '학습시간' in df.columns:
        # 최신 연도 데이터만 추출
        latest_year = df['연도'].max()
        latest_data = df[df['연도'] == latest_year].copy()
        
        fig = px.scatter(
            latest_data,
            x='전년대비변화율',
            y='학습시간',
            hover_data=['멤버사명'],
            title='멤버사별 학습시간 Matrix (변화율 vs 학습시간)',
            labels={
                '전년대비변화율': '전년 대비 변화율 (%)',
                '학습시간': '올해 학습시간 (시간)'
            }
        )
        
        # 사분면 구분선 추가 (평균 기준)
        if len(latest_data) > 0:
            avg_time = latest_data['학습시간'].mean()
            fig.add_hline(y=avg_time, line_dash="dash", line_color="gray", 
                         annotation_text=f"평균 학습시간: {avg_time:.0f}시간")
            fig.add_vline(x=0, line_dash="dash", line_color="gray", 
                         annotation_text="변화 없음")
        
        return fig
    return None

def create_popular_cards_chart(df, top_n=10):
    """인기 학습카드 Top N 차트"""
    if df is None or df.empty:
        return None
    
    # 학습자 수 기준으로 정렬
    if '학습자수' in df.columns:
        top_cards = df.nlargest(top_n, '학습자수')
        
        fig = px.bar(
            top_cards,
            x='학습자수',
            y='학습카드명',
            orientation='h',
            title=f'인기 학습카드 Top {top_n}',
            labels={'학습자수': '학습자 수', '학습카드명': '학습카드명'}
        )
        
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        return fig
    return None

def create_org_learning_chart(df):
    """조직별 평균 학습시간 차트"""
    if df is None or df.empty or '조직' not in df.columns:
        return None
    
    org_stats = df.groupby('조직')['학습시간'].agg(['mean', 'count']).reset_index()
    org_stats.columns = ['조직', '평균학습시간', '인원수']
    
    fig = px.bar(
        org_stats,
        x='조직',
        y='평균학습시간',
        title='조직별 평균 학습시간',
        labels={'평균학습시간': '평균 학습시간 (시간)', '조직': '조직'},
        text='평균학습시간'
    )
    
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig.update_xaxes(tickangle=45)
    
    return fig

def create_position_learning_chart(df):
    """직책별 평균 학습시간 차트 (임원, 팀장, 구성원 순서)"""
    if df is None or df.empty or '직책' not in df.columns:
        return None
    
    position_stats = df.groupby('직책')['학습시간'].mean().reset_index()
    
    # 직책 순서 정의 (임원, 팀장, 구성원)
    position_order = ["임원", "팀장", "구성원"]
    position_stats['직책'] = pd.Categorical(position_stats['직책'], categories=position_order, ordered=True)
    position_stats = position_stats.sort_values('직책').dropna()
    
    fig = px.bar(
        position_stats,
        x='직책',
        y='학습시간',
        title='직책별 평균 학습시간',
        labels={'학습시간': '평균 학습시간 (시간)', '직책': '직책'},
        text='학습시간'
    )
    
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    
    return fig

def create_individual_distribution_chart(df):
    """개인별 학습시간 분포 히스토그램"""
    if df is None or df.empty or '학습시간' not in df.columns:
        return None
    
    fig = px.histogram(
        df,
        x='학습시간',
        nbins=30,
        title='개인별 학습시간 분포',
        labels={'학습시간': '학습시간 (시간)', 'count': '인원 수'}
    )
    
    # 평균선 추가
    avg_time = df['학습시간'].mean()
    fig.add_vline(x=avg_time, line_dash="dash", line_color="red", 
                 annotation_text=f"평균: {avg_time:.0f}시간")
    
    return fig

def create_change_group_chart(df, change_groups):
    """변화군별 학습시간 추이 차트"""
    if df is None or df.empty or not change_groups:
        return None
    
    # 변화군별 평균 학습시간 계산
    group_data = []
    for group_name, members in change_groups.items():
        if members:
            group_df = df[df['개인ID'].isin(members)]
            group_data.append({
                '변화군': group_name,
                '24년평균': group_df.get('24년학습시간', group_df.get('2024학습시간', 0)).mean() if '24년학습시간' in group_df.columns else 0,
                '25년평균': group_df.get('25년학습시간', group_df.get('2025학습시간', 0)).mean() if '25년학습시간' in group_df.columns else 0,
                '인원수': len(members)
            })
    
    if not group_data:
        return None
    
    group_df = pd.DataFrame(group_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='24년',
        x=group_df['변화군'],
        y=group_df['24년평균'],
        text=group_df['인원수'],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='25년',
        x=group_df['변화군'],
        y=group_df['25년평균'],
        text=group_df['인원수'],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='변화군별 학습시간 비교 (24년 vs 25년)',
        xaxis_title='변화군',
        yaxis_title='평균 학습시간 (시간)',
        barmode='group',
        hovermode='x unified'
    )
    
    return fig

def create_area_status_chart(df):
    """주요 영역별 학습 현황 차트"""
    if df is None or df.empty:
        return None
    
    if '영역명' in df.columns and '이수인원' in df.columns:
        fig = px.bar(
            df,
            x='영역명',
            y='이수인원',
            title='주요 영역별 이수 인원',
            labels={'이수인원': '이수 인원 (명)', '영역명': '영역'}
        )
        
        return fig
    
    return None

