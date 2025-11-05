"""
mySUNI Learning Report 자동화 대시보드
메인 애플리케이션
"""

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime

# 모듈 임포트
from modules.auth import check_authentication
from modules.file_uploader import render_file_upload_section, save_to_session
from modules.data_loader import *
from modules.charts import *
from modules.eda_analyzer import *
from modules.change_group_analyzer import classify_change_groups, get_change_group_statistics
from modules.gemini_insights import get_gemini_client, generate_chart_insight, generate_eda_insight

# 공통 필터 헬퍼: 멤버사 선택 적용
def apply_company_filter(df):
    try:
        if df is None:
            return df
        company = st.session_state.get('selected_company', None)
        if company and '멤버사명' in df.columns:
            return df[df['멤버사명'] == company]
        return df
    except Exception:
        return df

# 페이지 설정
st.set_page_config(
    page_title="mySUNI Learning Report",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 인증 확인
auth_status = check_authentication()
if not auth_status:
    st.stop()

# 로그아웃 후 세션 상태 초기화
if 'authenticator' in st.session_state:
    authenticator = st.session_state.authenticator
    if authenticator and hasattr(authenticator, 'logout'):
        # 로그아웃이 발생했는지 확인 (세션에서 제거됨)
        if 'authentication_status' not in st.session_state:
            # 로그아웃 상태 - 로그인 페이지로 돌아감
            st.session_state.clear()
            st.rerun()

# 사이드바 구조 재구성 (먼저 렌더링)
# 페이지 상태 먼저 확인 (사이드바 버튼이 작동하도록)
current_page = st.session_state.get('current_page', None)
show_upload = st.session_state.get('show_upload', False)

# HOME 버튼 (맨 위)
if st.sidebar.button("🏠 HOME", use_container_width=True, type="primary", key="home_btn"):
    st.session_state['current_page'] = 'home'
    st.session_state['show_upload'] = False
    st.rerun()

# 파일 업로드 버튼 (HOME 아래)
render_file_upload_section()

# 업로드 결과 섹션 (리포트 결과 → 업로드 결과로 이름 변경, 멤버사 선택보다 위로)
# 멤버사 선택값 세션에서 복원
selected_company = st.session_state.get('selected_company', None)
with st.sidebar.expander("📊 업로드 결과", expanded=False):
    has_data = 'uploaded_data' in st.session_state and st.session_state.uploaded_data
    
    if has_data:
        st.success("✓ 데이터 로드 완료")
        
        # 업로드된 파일 목록 표시
        uploaded_count = len([k for k in st.session_state.uploaded_data.keys() if not k.endswith('_info')])
        st.metric("업로드된 파일 수", f"{uploaded_count}개")
        
        # 데이터 요약
        from modules.data_loader import get_annual_learning_data, get_individual_data
        annual_df = apply_company_filter(get_annual_learning_data())
        individual_df = apply_company_filter(get_individual_data())
        
        if annual_df is not None:
            if '학습시간' in annual_df.columns:
                total_time = annual_df['학습시간'].sum()
                st.metric("총 학습시간", f"{total_time:,.0f}시간")
        
        if individual_df is not None:
            num_learners = len(individual_df)
            st.metric("학습자 수", f"{num_learners:,}명")
    else:
        st.info("데이터를 업로드하세요")
        st.caption("파일 업로드 섹션에서 데이터를 업로드하고 '파일 데이터 로드' 버튼을 클릭하세요")

# 멤버사 선택 (업로드 결과 아래로 이동)
with st.sidebar.expander("📋 멤버사 선택", expanded=False):
    company_list = get_company_list()
    selected_company = st.session_state.get('selected_company', None)
    if company_list:
        temp_selection = st.selectbox(
            "멤버사 선택",
            ["전체"] + company_list,
            index=(0 if not selected_company else (["전체"] + company_list).index(selected_company) if selected_company in company_list else 0)
        )
        col_a, col_b = st.columns([1,1])
        with col_a:
            if st.button("적용", use_container_width=True, key="apply_company_filter"):
                if temp_selection == "전체":
                    st.session_state['selected_company'] = None
                else:
                    st.session_state['selected_company'] = temp_selection
                st.rerun()
        with col_b:
            if st.button("초기화", use_container_width=True, key="reset_company_filter"):
                st.session_state['selected_company'] = None
                st.rerun()
        # 현재 적용 상태 표시
        current = st.session_state.get('selected_company', None)
        st.caption(f"현재 적용: {'전체' if not current else current}")

# 리포트 조회 섹션 (새로 추가)
with st.sidebar.expander("📈 리포트 조회", expanded=False):
    st.caption("업로드된 데이터를 기반으로 리포트를 조회합니다")
    
    has_data_for_report = 'uploaded_data' in st.session_state and st.session_state.uploaded_data
    
    if has_data_for_report:
        if st.button("📊 리포트 조회하기", use_container_width=True, type="primary", key="report_view_btn"):
            st.session_state['current_page'] = 'report'
            st.session_state['show_upload'] = False  # 업로드 화면 끄기
            st.rerun()
    else:
        st.info("데이터를 먼저 업로드하세요")
        st.caption("파일 업로드를 통해 데이터를 업로드한 후 리포트를 조회할 수 있습니다")

# 리포트 다운로드 섹션 (PDF 생성 → 리포트 다운로드로 변경)
with st.sidebar.expander("📄 리포트 다운로드", expanded=False):
    st.caption("PDF 리포트를 생성하고 다운로드합니다")
    
    has_data_for_pdf = 'uploaded_data' in st.session_state and st.session_state.uploaded_data
    
    if has_data_for_pdf:
        # PDF 리포트 다운로드 선택
        pdf_option = st.selectbox(
            "PDF 리포트 다운로드",
            ["선택하세요", "전체 리포트 다운로드", "멤버사별 리포트 다운로드"],
            key="pdf_option"
        )
        
        if pdf_option != "선택하세요":
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("멤버사명", value="전체", key="pdf_company")
            
            with col2:
                period = st.selectbox(
                    "분석 기간",
                    ["2025년 상반기", "2025년 하반기", "2024년 상반기", "2024년 하반기"],
                    key="pdf_period"
                )
            
            include_insights = st.checkbox("AI 인사이트 포함", value=True, key="pdf_insights")
            
            if st.button("📥 PDF 리포트 다운로드", type="primary", use_container_width=True, key="pdf_generate_btn"):
                from modules.pdf_generator import collect_report_data, create_pdf_report
                
                try:
                    with st.spinner("PDF 리포트 생성 중..."):
                        # 리포트 데이터 수집
                        report_data = collect_report_data()
                        report_data['company_name'] = company_name
                        report_data['period'] = period
                        
                        # 인사이트 포함 여부
                        if not include_insights and 'insights' in report_data:
                            report_data['insights'] = {}
                        
                        # PDF 생성
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"Learning_Report_{company_name}_{timestamp}.pdf"
                        output_path = create_pdf_report(report_data, filename)
                        
                        # 파일 읽기
                        with open(output_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                        
                        # 다운로드 버튼
                        st.success("PDF 생성 완료!")
                        st.download_button(
                            label="📥 PDF 다운로드",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"PDF 생성 중 오류: {str(e)}")
    else:
        st.warning("먼저 데이터를 업로드하세요")

# 샘플 데이터 생성 버튼 (이름 변경: 샘플 데이터 로드 → 샘플 데이터 생성)
with st.sidebar.expander("🧪 샘플 데이터", expanded=False):
    st.caption("샘플 데이터를 빠르게 로드하여 테스트할 수 있습니다.")
    
    if st.button("📊 샘플 데이터 생성", use_container_width=True, type="secondary", key="sample_data_load_btn"):
        import os
        from modules.file_uploader import save_to_session
        
        sample_dir = "sample_data"
        if not os.path.exists(sample_dir):
            st.error("샘플 데이터가 없습니다. 먼저 `create_sample_data.py`를 실행하여 샘플 데이터를 생성하세요.")
        else:
            try:
                # 샘플 파일 매핑
                file_mapping = {
                    'annual_learning': f"{sample_dir}/1. 연간 학습시간.xlsx",
                    'monthly_learning': f"{sample_dir}/2. 월별 학습시간.xlsx",
                    'category_learning': f"{sample_dir}/3. 카테고리별 학습시간.xlsx",
                    'popular_cards': f"{sample_dir}/4. 인기학습카드.xlsx",
                    'search_keywords': f"{sample_dir}/5. 검색어.xlsx",
                    'individual_raw': f"{sample_dir}/6. 개인별 학습시간 raw.xlsx",
                    'card_raw': f"{sample_dir}/7. 카드별 학습시간 raw.xlsx",
                    'badge_raw': f"{sample_dir}/8. Badge별 학습시간 raw.xlsx",
                    'individual_full_raw': f"{sample_dir}/9. 개인별 학습 전체 raw.xlsx"
                }
                
                from modules.file_uploader import FILE_TYPES, validate_file_structure, normalize_columns
                import pandas as pd
                
                loaded_count = 0
                
                with st.spinner("샘플 데이터 로드 중..."):
                    if 'uploaded_data' not in st.session_state:
                        st.session_state.uploaded_data = {}
                    
                    for file_key, file_path in file_mapping.items():
                        if os.path.exists(file_path):
                            try:
                                # 직접 파일 경로로 읽기
                                df = pd.read_excel(file_path, engine='openpyxl')
                                
                                if df is not None and not df.empty:
                                    file_info = FILE_TYPES[file_key]
                                    # 1) 컬럼 표준화
                                    df_norm = normalize_columns(df, file_info['required_columns'])
                                    # 2) 검증
                                    is_valid, message = validate_file_structure(
                                        df_norm,
                                        file_info['required_columns']
                                    )
                                    
                                    if is_valid:
                                        # 3) 후처리: 분→시간, 연월→월
                                        try:
                                            if '학습시간' in df_norm.columns and '학습시간(분)' in df.columns:
                                                df_norm['학습시간'] = pd.to_numeric(df_norm['학습시간'], errors='coerce').fillna(0) / 60.0
                                        except Exception:
                                            pass
                                        try:
                                            if '월' in df_norm.columns:
                                                max_val = pd.to_numeric(df_norm['월'], errors='coerce').max()
                                                if pd.notna(max_val) and max_val > 12:
                                                    df_norm['월'] = pd.to_numeric(df_norm['월'], errors='coerce').astype('Int64')
                                                    df_norm['월'] = df_norm['월'].astype(str).str[-2:]
                                                    df_norm['월'] = pd.to_numeric(df_norm['월'], errors='coerce').astype('Int64')
                                        except Exception:
                                            pass

                                        st.session_state.uploaded_data[file_key] = df_norm
                                        st.session_state.uploaded_data[f"{file_key}_info"] = file_info
                                        loaded_count += 1
                                    else:
                                        st.warning(f"{file_info['name']}: {message}")
                            except Exception as e:
                                file_info = FILE_TYPES.get(file_key, {'name': file_key})
                                st.warning(f"{file_info['name']} 로드 실패: {str(e)}")
                    
                    # 결과 메시지
                    if loaded_count > 0:
                        # 샘플 데이터 생성 완료 후 자동으로 리포트 화면으로 이동
                        st.success("✅ 샘플 데이터가 생성되었습니다. 샘플 리포트를 확인하세요.")
                        st.session_state['current_page'] = 'report'  # 리포트 페이지로 이동
                        st.session_state['show_upload'] = False  # 업로드 화면 끄기
                        st.rerun()
                    else:
                        st.error("샘플 데이터를 로드할 수 없습니다.")
            except Exception as e:
                st.error(f"샘플 데이터 로드 중 오류: {str(e)}")

# 페이지 상태 확인 (위에서 이미 확인했으므로 업데이트만)
show_upload = st.session_state.get('show_upload', False)
has_data = 'uploaded_data' in st.session_state and st.session_state.uploaded_data

# 파일 업로드 화면 표시 (최우선 처리 - HOME 화면보다 먼저)
if show_upload:
    st.session_state['current_page'] = None  # 업로드 페이지에서는 탭 메뉴 사용
    # 파일 업로드 화면 표시
    from modules.file_uploader import render_file_upload_main
    render_file_upload_main()
    st.stop()

# 리포트 조회 페이지 처리 (파일 업로드 이후, HOME보다 먼저)
if current_page == 'report':
    # 리포트 조회 페이지에서는 탭 메뉴와 리포트 화면 표시
    st.session_state['show_upload'] = False  # 업로드 화면 끄기
    # current_page를 None으로 설정하여 탭 메뉴 사용 (리포트 화면 표시를 위해)
    st.session_state['current_page'] = None
    # 리포트 화면은 아래 탭 메뉴에서 처리됨

# 최초 로그인 시 HOME 화면 표시 (데이터가 없을 때만)
if current_page is None and not has_data:
    current_page = 'home'
    st.session_state['current_page'] = 'home'
elif current_page is None and has_data:
    # 데이터가 있으면 리포트 페이지로
    current_page = None

# HOME 화면
if current_page == 'home':
    st.title("🏠 mySUNI Learning Report 자동화 대시보드")
    st.markdown("---")
    
    st.header("📋 개요")
    st.markdown("""
    ### 목적
    mySUNI 그룹 학습플랫폼의 이용 데이터를 기반으로 각 멤버사의 학습 현황을 자동으로 분석하여 
    Learning Report를 제공하는 자동화 대시보드입니다.
    
    ### 주요 기능
    - **자동화된 리포트 생성**: 수동 작업 대신 자동으로 리포트 생성
    - **다양한 분석 제공**: 학습시간, 조직/직책/개인별 분석, 변화군 분석 등
    - **AI 기반 인사이트**: Google Gemini를 활용한 자동 인사이트 생성
    - **PDF 리포트 다운로드**: 완성된 리포트를 PDF로 다운로드
    """)
    
    st.header("📊 리포트 구성 항목")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 기본 분석
        - 최근 4개년 학습시간 현황 및 추이
        - 그룹/각 사별 학습시간 Matrix
        - 인기 콘텐츠 (학습카드, 검색어)
        
        #### 조직 분석
        - 조직별(사업부별) 평균 학습시간
        - 조직별 학습 특징 분석
        """)
    
    with col2:
        st.markdown("""
        #### 개인 분석
        - 직책별(임원/팀장/구성원) 평균 학습시간
        - 개인별 학습시간 분포
        - 학습시간 변화군 분석 (24년 vs 25년)
        
        #### 주요 영역
        - 경영철학, AI/DT, 공통직무역량 학습 현황
        """)
    
    st.header("📁 구성 데이터")
    st.markdown("""
    리포트 생성에 필요한 데이터 파일은 다음과 같습니다:
    
    1. **그룹/멤버사 연간 학습시간**: 최근 4개년 학습시간 데이터
    2. **멤버사 월별 학습시간**: 월별 상세 데이터
    3. **학습 카테고리별 학습시간**: 카테고리별 집계 데이터
    4. **인기 학습카드**: 인기 콘텐츠 데이터
    5. **검색어 데이터**: 연도별 검색어 데이터
    6. **주요 영역 인증/이수 현황표**: 영역별 인증 현황
    7. **개인별 학습시간 raw data**: 개인별 기본 데이터
    8. **카드별 학습시간 raw data**: 학습카드별 상세 정보
    9. **Badge별 학습시간 raw data**: Badge별 정보
    10. **개인별 학습 전체 raw data**: 변화군 분석용 데이터
    """)
    
    st.header("🚀 시작하기")
    st.markdown("""
    ### 1단계: 데이터 업로드
    - 사이드바의 **"📁 파일 업로드"** 버튼을 클릭하세요
    - 또는 **"🧪 샘플 데이터"** 메뉴에서 샘플 데이터를 로드할 수 있습니다
    
    ### 2단계: 리포트 조회
    - 데이터 업로드 후 사이드바의 **"📈 리포트 조회"** 메뉴에서 리포트를 조회하세요
    - 상단 탭을 통해 다양한 분석 결과를 확인할 수 있습니다
    
    ### 3단계: PDF 생성
    - 사이드바의 **"📄 PDF 생성"** 메뉴에서 최종 리포트를 PDF로 다운로드하세요
    """)
    
    st.info("💡 **팁**: 처음 사용하시는 경우 샘플 데이터를 로드하여 기능을 먼저 테스트해보세요!")
    
    st.stop()

# 탭 메뉴 (항상 표시) - 파일 업로드와 리포트 다운로드 제거
tabs = [
    "🏠 개요",
    "📈 학습시간 현황",
    "📊 Matrix 분석",
    "🔥 인기 콘텐츠",
    "🏢 조직별 분석",
    "👔 직책별 분석",
    "👤 개인별 분석",
    "📉 변화군 분석"
]

selected_tab = option_menu(
    menu_title=None,
    options=tabs,
    icons=['house', 'graph-up', 'grid', 'fire', 'building', 'briefcase', 'person', 'arrow-down-up'],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal"
)

# 리포트 화면 표시 (일반 대시보드 탭들)
st.title("📊 mySUNI Learning Report 자동화 대시보드")
st.markdown("---")

# 데이터 로드 확인
has_data = 'uploaded_data' in st.session_state and st.session_state.uploaded_data

if not has_data:
    st.info("👈 사이드바의 '📁 파일 업로드' 버튼을 클릭하여 데이터 파일들을 업로드하세요.")
    
    # 안내 섹션
    st.markdown("### 사용 가이드")
    st.markdown("""
    1. **파일 업로드**: 사이드바의 "📁 파일 업로드" 버튼을 클릭하여 데이터 파일들을 업로드하세요
    2. **데이터 로드**: 모든 파일 업로드 후 "📥 파일 데이터 로드" 버튼을 클릭하세요
    3. **분석 확인**: 데이터가 로드되면 상단 탭에서 다양한 분석 결과를 확인할 수 있습니다
    4. **리포트 다운로드**: 사이드바의 "📄 리포트 다운로드" 메뉴에서 최종 리포트를 PDF로 다운로드할 수 있습니다
    """)
else:
    # 개요 탭
    if selected_tab == "🏠 개요":
        st.header("전체 학습 현황 요약")
        
        annual_df = get_annual_learning_data()
        individual_df = get_individual_data()
        
        if annual_df is not None:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if '학습시간' in annual_df.columns:
                    total_time = annual_df['학습시간'].sum()
                    st.metric("총 학습시간", f"{total_time:,.0f}시간")
            
            with col2:
                if '멤버사명' in annual_df.columns:
                    num_companies = annual_df['멤버사명'].nunique()
                    st.metric("멤버사 수", f"{num_companies}개")
            
            with col3:
                if individual_df is not None and '학습시간' in individual_df.columns:
                    avg_time = individual_df['학습시간'].mean()
                    st.metric("평균 학습시간", f"{avg_time:.1f}시간")
            
            with col4:
                if individual_df is not None:
                    num_learners = len(individual_df)
                    st.metric("학습자 수", f"{num_learners:,}명")
        
        # 최근 3개년 추이는 개요에서 제거됨

    # 학습시간 현황 탭
    elif selected_tab == "📈 학습시간 현황":
        st.header("학습시간 현황 분석")
        
        annual_df = get_annual_learning_data()
        
        if annual_df is not None:
            annual_df = preprocess_annual_data(annual_df)
            
            # 최근 3개년 인당 평균 학습시간 (세로 막대)
            st.subheader("최근 3개년 인당 평균 학습시간")
            individual_full = apply_company_filter(get_individual_full_raw_data())
            if individual_full is None:
                individual_full = apply_company_filter(get_individual_data())
            avg_year = None
            if individual_full is not None and '연도' in individual_full.columns and '학습시간' in individual_full.columns:
                if selected_company and '멤버사명' in individual_full.columns:
                    individual_full = individual_full[individual_full['멤버사명'] == selected_company]
                avg_year = (
                    individual_full.groupby('연도')['학습시간']
                    .mean()
                    .reset_index()
                    .sort_values('연도')
                )
                import plotly.express as px
                fig_bar = px.bar(avg_year.tail(3), x='연도', y='학습시간', title='최근 3개년 인당 평균 학습시간', labels={'학습시간':'시간'})
                st.plotly_chart(fig_bar, use_container_width=True)
            
            st.subheader("멤버사별 인당 평균 학습시간")
            individual_df2 = get_individual_data()  # 전체 멤버사 유지 요구사항
            if individual_df2 is not None:
                individual_df2 = preprocess_individual_data(individual_df2)
                if '멤버사명' in individual_df2.columns and '학습시간' in individual_df2.columns:
                    company_avg = (
                        individual_df2.groupby('멤버사명')['학습시간']
                        .mean()
                        .sort_values(ascending=False)
                    )
                    st.dataframe(company_avg.reset_index().rename(columns={'학습시간':'인당 평균(시간)'}), use_container_width=True)

    # Matrix 분석 탭
    elif selected_tab == "📊 Matrix 분석":
        st.header("그룹/각 사별 인당 평균 학습시간 Matrix (X: 전년 대비 변화, Y: 인당 평균 학습시간)")
        
        annual_df = get_annual_learning_data()
        
        if annual_df is not None:
            import pandas as pd
            import plotly.express as px
            # 개인 전체 raw가 있으면 2024/2025 기준으로 회사별 인당 평균 및 변화율 계산
            indiv_full = get_individual_full_raw_data()
            scatter_df = None
            base_year = 2024
            target_year = 2025
            if indiv_full is not None and all(c in indiv_full.columns for c in ['멤버사명','연도','학습시간']):
                df_f = indiv_full.copy()
                df_f = df_f[df_f['연도'].isin([base_year, target_year])]
                avg_by = df_f.groupby(['멤버사명','연도'])['학습시간'].mean().reset_index()
                pivot = avg_by.pivot(index='멤버사명', columns='연도', values='학습시간').reset_index()
                if base_year in pivot.columns and target_year in pivot.columns:
                    pivot['변화(%)'] = ((pivot[target_year] - pivot[base_year]) / (pivot[base_year].replace(0, pd.NA)) * 100).fillna(0)
                    scatter_df = pivot.rename(columns={target_year:'올해(시간)'})[['멤버사명','변화(%)','올해(시간)']]
            # 폴백: 개인 raw만 있는 경우 최신 연도 평균으로 Y만 표시, 변화는 0
            if scatter_df is None:
                indiv = get_individual_data()
                if indiv is not None and '멤버사명' in indiv.columns and '학습시간' in indiv.columns:
                    indiv_proc = preprocess_individual_data(indiv)
                    latest_avg = indiv_proc.groupby('멤버사명')['학습시간'].mean().reset_index().rename(columns={'학습시간':'올해(시간)'})
                    latest_avg['변화(%)'] = 0
                    scatter_df = latest_avg[['멤버사명','변화(%)','올해(시간)']]

            fig = None
            if scatter_df is not None and not scatter_df.empty:
                fig = px.scatter(scatter_df, x='변화(%)', y='올해(시간)', text='멤버사명',
                                 labels={'올해(시간)':'인당 평균(시간)'},
                                 title=f"{target_year} 인당 평균 vs {base_year} 대비 변화")
                fig.update_traces(textposition='top center')
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    # 인기 콘텐츠 탭
    elif selected_tab == "🔥 인기 콘텐츠":
        st.header("구성원 관심 콘텐츠")
        
        popular_df = get_popular_cards_data()
        search_df = get_search_keywords_data()
        
        if popular_df is not None:
            st.subheader("인기 학습카드 Top 10")
            fig = create_popular_cards_chart(popular_df, top_n=10)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        if search_df is not None:
            st.subheader("인기 검색어 (연도별)")
            if '연도' in search_df.columns and '검색어' in search_df.columns and '검색횟수' in search_df.columns:
                for year in [2025, 2024]:
                    year_df = search_df[search_df['연도'] == year]
                    if not year_df.empty:
                        st.markdown(f"#### {year}년")
                        st.dataframe(year_df.nlargest(20, '검색횟수')[['검색어','검색횟수']], use_container_width=True)

    # 조직별 분석 탭
    elif selected_tab == "🏢 조직별 분석":
        st.header("조직별 학습 특징 분석")
        
        individual_df = apply_company_filter(get_individual_data())
        
        if individual_df is not None:
            individual_df = preprocess_individual_data(individual_df)
            if selected_company and '멤버사명' in individual_df.columns:
                individual_df = individual_df[individual_df['멤버사명'] == selected_company]
            
            st.subheader("조직별 평균 학습시간")
            fig = create_org_learning_chart(individual_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("조직별 통계 분석")
            org_stats = analyze_organization_characteristics(individual_df)
            if org_stats is not None:
                st.dataframe(org_stats, use_container_width=True)

    # 직책별 분석 탭
    elif selected_tab == "👔 직책별 분석":
        st.header("직책별 학습 특징 분석")
        
        individual_df = apply_company_filter(get_individual_data())
        
        if individual_df is not None:
            individual_df = preprocess_individual_data(individual_df)
            if selected_company and '멤버사명' in individual_df.columns:
                individual_df = individual_df[individual_df['멤버사명'] == selected_company]
            
            st.subheader("직책별 평균 학습시간")
            fig = create_position_learning_chart(individual_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("직책별 통계 분석")
            position_stats = analyze_position_characteristics(individual_df)
            if position_stats is not None:
                st.dataframe(position_stats, use_container_width=True)
                
                # Gemini 인사이트
                if st.button("🤖 직책별 특징 분석 (AI)", key="position_insight"):
                    client = get_gemini_client()
                    if client:
                        from modules.eda_analyzer import get_enhanced_eda_summary
                        stats_text = get_enhanced_eda_summary(position_stats, '직책별')
                        insight = generate_eda_insight(client, '직책별', stats_text)
                        if insight:
                            st.markdown("#### 💡 AI 분석 인사이트")
                            st.write(insight)
                    else:
                        st.error("Gemini API 키가 설정되지 않았습니다.")

    # 개인별 분석 탭
    elif selected_tab == "👤 개인별 분석":
        st.header("개인별 학습 특징 분석")
        
        individual_df = apply_company_filter(get_individual_data())
        
        if individual_df is not None:
            individual_df = preprocess_individual_data(individual_df)
            if selected_company and '멤버사명' in individual_df.columns:
                individual_df = individual_df[individual_df['멤버사명'] == selected_company]
            
            st.subheader("개인별 학습시간 분포")
            fig = create_individual_distribution_chart(individual_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("통계 분석")
            stats, low_learners, high_learners = analyze_individual_characteristics(individual_df)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 전체 통계")
                for key, value in stats.items():
                    if isinstance(value, (int, float)) and '수' not in key and '평균' not in key and '중위' not in key:
                        st.metric(key, f"{value:.2f}")
                    elif isinstance(value, (int, float)):
                        st.metric(key, f"{value:,.0f}")
            
            with col2:
                st.markdown("#### 저학습자/고학습자 구분")
                st.metric("저학습자 수", f"{stats.get('저학습자수', 0):,}명")
                st.metric("고학습자 수", f"{stats.get('고학습자수', 0):,}명")
                if stats.get('저학습자평균'):
                    st.metric("저학습자 평균", f"{stats['저학습자평균']:.1f}시간")
                if stats.get('고학습자평균'):
                    st.metric("고학습자 평균", f"{stats['고학습자평균']:.1f}시간")
            
            # Gemini 인사이트
            if st.button("🤖 개인별 특징 분석 (AI)", key="individual_insight"):
                client = get_gemini_client()
                if client:
                    stats_text = "\n".join([f"{k}: {v}" for k, v in stats.items()])
                    insight = generate_eda_insight(client, '개인별', stats_text)
                    if insight:
                        st.markdown("#### 💡 AI 분석 인사이트")
                        st.write(insight)
                else:
                    st.error("Gemini API 키가 설정되지 않았습니다.")

    # 변화군 분석 탭
    elif selected_tab == "📉 변화군 분석":
        st.header("학습시간 변화군 분석")
        
        # 22-25년도 데이터가 필요
        individual_full_df = apply_company_filter(get_individual_full_raw_data())
        
        if individual_full_df is None:
            individual_df = get_individual_data()
            st.info("22-25년도 학습시간 데이터가 필요합니다. 개인별 학습 전체 raw data를 업로드하거나, 개인별 학습시간 데이터에 연도 컬럼이 포함되어야 합니다.")
        else:
            if selected_company and '멤버사명' in individual_full_df.columns:
                individual_full_df = individual_full_df[individual_full_df['멤버사명'] == selected_company]
            change_groups = classify_change_groups(individual_full_df)
            
            if change_groups:
                st.subheader("변화군별 인원 수")
                
                group_summary = pd.DataFrame([
                    {'변화군': group, '인원수': len(members)}
                    for group, members in change_groups.items() if members
                ])
                
                st.dataframe(group_summary, use_container_width=True)
                
                # 변화군별 통계
                stats_df = get_change_group_statistics(individual_full_df, change_groups)
                if stats_df is not None and not stats_df.empty:
                    st.subheader("변화군별 통계")
                    st.dataframe(stats_df, use_container_width=True)
                    
                    # 차트
                    fig = create_change_group_chart(individual_full_df, change_groups)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                # Gemini 인사이트
                if st.button("🤖 변화군별 특징 분석 (AI)", key="change_group_insight"):
                    client = get_gemini_client()
                    if client:
                        stats_text = stats_df.to_string() if stats_df is not None else ""
                        insight = generate_eda_insight(client, '변화군별', stats_text)
                        if insight:
                            st.markdown("#### 💡 AI 분석 인사이트")
                            st.write(insight)
                    else:
                        st.error("Gemini API 키가 설정되지 않았습니다.")

    # 주요 영역별 탭
    elif selected_tab == "🎯 주요 영역별":
        st.header("주요 영역별 학습 현황")
        
        area_df = get_area_status_data()
        
        if area_df is not None:
            fig = create_area_status_chart(area_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("영역별 상세 현황")
            st.dataframe(area_df, use_container_width=True)

        # 리포트 다운로드 탭 제거 (사이드바로 이동)
        # 해당 탭은 사이드바의 "리포트 다운로드" 섹션으로 이동됨
        if False:  # 더 이상 사용하지 않음
            pass
        elif selected_tab == "📄 리포트 다운로드_DEPRECATED":
            st.header("PDF 리포트 생성 및 다운로드")
            
            from modules.pdf_generator import collect_report_data, create_pdf_report
            
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("멤버사명", value="전체")
                period = st.selectbox("분석 기간", ["2025년 상반기", "2025년 하반기", "2024년 상반기", "2024년 하반기"])
            
            with col2:
                include_insights = st.checkbox("AI 인사이트 포함", value=True)
                include_all_charts = st.checkbox("모든 차트 포함", value=True)
            
            if st.button("📄 PDF 리포트 생성", type="primary"):
                if not has_data:
                    st.error("먼저 데이터를 업로드하고 로드해주세요.")
                else:
                    try:
                        with st.spinner("PDF 리포트 생성 중..."):
                            # 리포트 데이터 수집
                            report_data = collect_report_data()
                            report_data['company_name'] = company_name
                            report_data['period'] = period
                            
                            # 인사이트 포함 여부
                            if not include_insights and 'insights' in report_data:
                                report_data['insights'] = {}
                            
                            # PDF 생성
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"Learning_Report_{company_name}_{timestamp}.pdf"
                            output_path = create_pdf_report(report_data, filename)
                            
                            # 파일 읽기
                            with open(output_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                            
                            # 다운로드 버튼
                            st.success("PDF 리포트가 생성되었습니다!")
                            st.download_button(
                                label="📥 PDF 다운로드",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"PDF 생성 중 오류 발생: {str(e)}")
                        st.exception(e)
            
            st.markdown("---")
            st.markdown("""
            ### PDF 리포트 포함 내용:
            - 전체 학습 현황 요약
            - 학습시간 현황 및 추이
            - Matrix 분석
            - 인기 콘텐츠
            - 조직별/직책별/개인별 분석
            - 변화군 분석
            - 주요 영역별 학습 현황
            - AI 생성 인사이트 (선택)
            """)

