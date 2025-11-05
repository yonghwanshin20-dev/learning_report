"""
PDF 리포트 생성 모듈
대시보드의 모든 분석 결과를 PDF로 변환
"""

import streamlit as st
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import cm
import plotly.graph_objects as go
from io import BytesIO
import base64
import pandas as pd
from datetime import datetime
import os

def plotly_to_image(fig, width=800, height=600):
    """Plotly 차트를 이미지로 변환"""
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height)
        return BytesIO(img_bytes)
    except Exception as e:
        st.warning(f"차트 이미지 변환 실패: {str(e)}")
        return None

def create_pdf_report(data_dict, output_path="Learning_Report.pdf"):
    """
    PDF 리포트 생성
    
    Args:
        data_dict: 리포트에 포함할 데이터 딕셔너리
            - charts: 차트 딕셔너리 {title: fig}
            - insights: 인사이트 딕셔너리 {section: text}
            - summary: 요약 통계
            - company_name: 멤버사명
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    
    # 스타일 정의
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#366092'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    normal_style = styles['Normal']
    
    # 커버 페이지
    story.append(Paragraph("mySUNI Learning Report", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    company_name = data_dict.get('company_name', '전체')
    story.append(Paragraph(f"멤버사: {company_name}", heading_style))
    story.append(Spacer(1, 0.3*inch))
    
    report_date = datetime.now().strftime("%Y년 %m월 %d일")
    story.append(Paragraph(f"리포트 생성일: {report_date}", normal_style))
    
    period = data_dict.get('period', '2025년 상반기')
    story.append(Paragraph(f"분석 기간: {period}", normal_style))
    story.append(PageBreak())
    
    # 목차
    story.append(Paragraph("목차", heading_style))
    toc_items = [
        "1. 전체 학습 현황 요약",
        "2. 학습시간 현황",
        "3. Matrix 분석",
        "4. 인기 콘텐츠",
        "5. 조직별 분석",
        "6. 직책별 분석",
        "7. 개인별 분석",
        "8. 변화군 분석",
        "9. 주요 영역별 학습 현황"
    ]
    for item in toc_items:
        story.append(Paragraph(item, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(PageBreak())
    
    # 1. 전체 학습 현황 요약
    story.append(Paragraph("1. 전체 학습 현황 요약", heading_style))
    
    if 'summary' in data_dict:
        summary = data_dict['summary']
        summary_text = f"""
        총 학습시간: {summary.get('total_time', 'N/A')}시간
        멤버사 수: {summary.get('num_companies', 'N/A')}개
        평균 학습시간: {summary.get('avg_time', 'N/A'):.1f}시간
        학습자 수: {summary.get('num_learners', 'N/A'):,}명
        """
        story.append(Paragraph(summary_text, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 연간 추이 차트
    if 'charts' in data_dict and 'annual_trend' in data_dict['charts']:
        fig = data_dict['charts']['annual_trend']
        img_buffer = plotly_to_image(fig, width=800, height=500)
        if img_buffer:
            img_buffer.seek(0)
            story.append(Image(img_buffer, width=16*cm, height=10*cm))
            story.append(Spacer(1, 0.3*inch))
    
    story.append(PageBreak())
    
    # 2. 학습시간 현황
    story.append(Paragraph("2. 학습시간 현황", heading_style))
    
    if 'insights' in data_dict and 'learning_time' in data_dict['insights']:
        insight_text = data_dict['insights']['learning_time']
        story.append(Paragraph("인사이트", subheading_style))
        story.append(Paragraph(insight_text, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    if 'charts' in data_dict and 'matrix' in data_dict['charts']:
        fig = data_dict['charts']['matrix']
        img_buffer = plotly_to_image(fig, width=800, height=600)
        if img_buffer:
            img_buffer.seek(0)
            story.append(Image(img_buffer, width=16*cm, height=12*cm))
            story.append(Spacer(1, 0.3*inch))
    
    story.append(PageBreak())
    
    # 3. 인기 콘텐츠
    story.append(Paragraph("3. 인기 콘텐츠", heading_style))
    
    if 'charts' in data_dict and 'popular_cards' in data_dict['charts']:
        fig = data_dict['charts']['popular_cards']
        img_buffer = plotly_to_image(fig, width=800, height=500)
        if img_buffer:
            img_buffer.seek(0)
            story.append(Image(img_buffer, width=16*cm, height=10*cm))
            story.append(Spacer(1, 0.3*inch))
    
    story.append(PageBreak())
    
    # 4. 조직별 분석
    story.append(Paragraph("4. 조직별 학습 특징 분석", heading_style))
    
    if 'charts' in data_dict and 'org_learning' in data_dict['charts']:
        fig = data_dict['charts']['org_learning']
        img_buffer = plotly_to_image(fig, width=800, height=500)
        if img_buffer:
            img_buffer.seek(0)
            story.append(Image(img_buffer, width=16*cm, height=10*cm))
            story.append(Spacer(1, 0.2*inch))
    
    if 'insights' in data_dict and 'organization' in data_dict['insights']:
        insight_text = data_dict['insights']['organization']
        story.append(Paragraph("인사이트", subheading_style))
        story.append(Paragraph(insight_text, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # 5. 직책별 분석
    story.append(Paragraph("5. 직책별 학습 특징 분석", heading_style))
    
    if 'charts' in data_dict and 'position_learning' in data_dict['charts']:
        fig = data_dict['charts']['position_learning']
        img_buffer = plotly_to_image(fig, width=800, height=500)
        if img_buffer:
            img_buffer.seek(0)
            story.append(Image(img_buffer, width=16*cm, height=10*cm))
            story.append(Spacer(1, 0.2*inch))
    
    if 'insights' in data_dict and 'position' in data_dict['insights']:
        insight_text = data_dict['insights']['position']
        story.append(Paragraph("인사이트", subheading_style))
        story.append(Paragraph(insight_text, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # 6. 개인별 분석
    story.append(Paragraph("6. 개인별 학습 특징 분석", heading_style))
    
    if 'charts' in data_dict and 'individual_distribution' in data_dict['charts']:
        fig = data_dict['charts']['individual_distribution']
        img_buffer = plotly_to_image(fig, width=800, height=500)
        if img_buffer:
            img_buffer.seek(0)
            story.append(Image(img_buffer, width=16*cm, height=10*cm))
            story.append(Spacer(1, 0.2*inch))
    
    if 'insights' in data_dict and 'individual' in data_dict['insights']:
        insight_text = data_dict['insights']['individual']
        story.append(Paragraph("인사이트", subheading_style))
        story.append(Paragraph(insight_text, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # 7. 변화군 분석
    story.append(Paragraph("7. 학습시간 변화군 분석", heading_style))
    
    if 'charts' in data_dict and 'change_group' in data_dict['charts']:
        fig = data_dict['charts']['change_group']
        img_buffer = plotly_to_image(fig, width=800, height=500)
        if img_buffer:
            img_buffer.seek(0)
            story.append(Image(img_buffer, width=16*cm, height=10*cm))
            story.append(Spacer(1, 0.2*inch))
    
    if 'insights' in data_dict and 'change_group' in data_dict['insights']:
        insight_text = data_dict['insights']['change_group']
        story.append(Paragraph("인사이트", subheading_style))
        story.append(Paragraph(insight_text, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # 8. 주요 영역별
    story.append(Paragraph("8. 주요 영역별 학습 현황", heading_style))
    
    if 'charts' in data_dict and 'area_status' in data_dict['charts']:
        fig = data_dict['charts']['area_status']
        img_buffer = plotly_to_image(fig, width=800, height=500)
        if img_buffer:
            img_buffer.seek(0)
            story.append(Image(img_buffer, width=16*cm, height=10*cm))
            story.append(Spacer(1, 0.2*inch))
    
    # 마지막 페이지 - 요약
    story.append(PageBreak())
    story.append(Paragraph("결론", heading_style))
    
    conclusion_text = """
    본 리포트는 mySUNI 플랫폼의 학습 데이터를 종합적으로 분석한 결과입니다.
    각 섹션에서 제시된 인사이트를 바탕으로 L&D 전략을 수립하시기 바랍니다.
    """
    story.append(Paragraph(conclusion_text, normal_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"생성일: {report_date}", normal_style))
    
    # PDF 빌드
    doc.build(story)
    return output_path

def collect_report_data():
    """현재 세션의 데이터를 수집하여 리포트 데이터 구조 생성"""
    from modules.data_loader import *
    from modules.charts import *
    from modules.eda_analyzer import *
    
    data_dict = {
        'charts': {},
        'insights': {},
        'summary': {},
        'company_name': '전체',
        'period': '2025년 상반기'
    }
    
    # 요약 통계
    annual_df = get_annual_learning_data()
    individual_df = get_individual_data()
    
    if annual_df is not None:
        if '학습시간' in annual_df.columns:
            data_dict['summary']['total_time'] = annual_df['학습시간'].sum()
        if '멤버사명' in annual_df.columns:
            data_dict['summary']['num_companies'] = annual_df['멤버사명'].nunique()
        if individual_df is not None:
            if '학습시간' in individual_df.columns:
                data_dict['summary']['avg_time'] = individual_df['학습시간'].mean()
            data_dict['summary']['num_learners'] = len(individual_df)
    
    # 차트 수집
    if annual_df is not None:
        fig = create_annual_trend_chart(annual_df)
        if fig:
            data_dict['charts']['annual_trend'] = fig
        
        fig = create_matrix_chart(annual_df)
        if fig:
            data_dict['charts']['matrix'] = fig
    
    popular_df = get_popular_cards_data()
    if popular_df is not None:
        fig = create_popular_cards_chart(popular_df)
        if fig:
            data_dict['charts']['popular_cards'] = fig
    
    if individual_df is not None:
        fig = create_org_learning_chart(individual_df)
        if fig:
            data_dict['charts']['org_learning'] = fig
        
        fig = create_position_learning_chart(individual_df)
        if fig:
            data_dict['charts']['position_learning'] = fig
        
        fig = create_individual_distribution_chart(individual_df)
        if fig:
            data_dict['charts']['individual_distribution'] = fig
    
    area_df = get_area_status_data()
    if area_df is not None:
        fig = create_area_status_chart(area_df)
        if fig:
            data_dict['charts']['area_status'] = fig
    
    # 변화군 차트
    individual_full_df = get_individual_full_raw_data()
    if individual_full_df is not None:
        from modules.change_group_analyzer import classify_change_groups
        change_groups = classify_change_groups(individual_full_df)
        if change_groups:
            fig = create_change_group_chart(individual_full_df, change_groups)
            if fig:
                data_dict['charts']['change_group'] = fig
    
    # 인사이트는 세션에서 가져오기
    if 'insights' in st.session_state:
        data_dict['insights'] = st.session_state.insights
    
    return data_dict

