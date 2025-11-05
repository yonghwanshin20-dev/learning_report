"""
파일 업로드 모듈
각 파일 종류별 업로드 기능
"""

import streamlit as st
import pandas as pd

# 파일 타입 정의 (요청하신 10개 파일명에 맞춘 권장 파일명 및 필수 컬럼 반영)
FILE_TYPES = {
    'annual_learning': {
        'name': '1. 연간 학습시간',
        'expected_filename': '1. 연간 학습시간.xlsx',
        'description': '최근 4개년 학습시간 (전년 대비 변화율, 상/하반기 포함)',
        'required_columns': ['멤버사명', '연도', '학습시간']
    },
    'monthly_learning': {
        'name': '2. 월별 학습시간',
        'expected_filename': '2. 월별 학습시간.xlsx',
        'description': '멤버사별 월별 학습시간',
        'required_columns': ['멤버사명', '연도', '월', '학습시간']
    },
    'category_learning': {
        'name': '3. 카테고리별 학습시간',
        'expected_filename': '3. 카테고리별 학습시간.xlsx',
        'description': '카테고리별 학습시간 및 학습자 수',
        # 업로드 데이터에 따라 학습자수 누락 가능 → 최소 컬럼으로 완화
        'required_columns': ['카테고리명', '학습시간']
    },
    'popular_cards': {
        'name': '4. 인기학습카드',
        'expected_filename': '4. 인기학습카드.xlsx',
        'description': '인기 학습카드 Top 리스트',
        # 평균학습시간/완료률은 선택 → 최소 컬럼으로 완화
        'required_columns': ['학습카드명', '학습자수']
    },
    'search_keywords': {
        'name': '5. 검색어',
        'expected_filename': '5. 검색어.xlsx',
        'description': '연도별 검색어 데이터',
        'required_columns': ['검색어', '연도', '검색횟수']
    },
    'individual_raw': {
        'name': '6. 개인별 학습시간 raw',
        'expected_filename': '6. 개인별 학습시간 raw.xlsx',
        'description': '개인별 학습시간 및 Demo/세부지표 (연도 포함 가능)',
        # 멤버사명은 없을 수도 있어 최소 컬럼만 강제
        'required_columns': ['개인ID', '학습시간']
    },
    'card_raw': {
        'name': '7. 카드별 학습시간 raw',
        'expected_filename': '7. 카드별 학습시간 raw.xlsx',
        'description': '학습카드별 상세 정보',
        # 일부 데이터는 ID/카테고리 누락 가능 → 최소 컬럼
        'required_columns': ['학습카드명']
    },
    'badge_raw': {
        'name': '8. Badge별 학습시간 raw',
        'expected_filename': '8. Badge별 학습시간 raw.xlsx',
        'description': 'Badge별 상세 정보',
        # 최소 컬럼
        'required_columns': ['Badge명']
    },
    'individual_full_raw': {
        'name': '9. 개인별 학습 전체 raw',
        'expected_filename': '9. 개인별 학습 전체 raw.xlsx',
        'description': '개인별 22-25년 전체 학습 내역 (변화군 분석용)',
        'required_columns': ['개인ID', '연도', '학습시간']
    }
}

# 업로드 컬럼 자동 매핑(별칭) 테이블
COLUMN_ALIASES = {
    # 공통
    '멤버사명': ['회사', '회사명', '멤버사', 'Group', 'Company', 'company', 'company_name', 'company_name_kor'],
    '연도': ['년도', 'Year', 'year', 'yr', 'base_year'],
    '월': ['월(숫자)', 'month', 'Month', 'mm', 'base_yearmonth'],
    '학습시간': ['시간', '학습 시간', 'LearningTime', 'learning_time', 'total_learning_time', 'time', 'learn_time'],
    # 카테고리
    '카테고리명': ['카테고리', '분류', 'Category', 'category', 'category_name', 'category_name_kor'],
    '학습자수': ['수강자수', '인원수', 'Learners', 'learners', 'num_learners', 'learner_count', '학습인원', '이수인원'],
    # 인기학습카드
    '학습카드명': ['카드명', '콘텐츠명', '과정명', 'CourseName', 'course_name', 'card_name', 'card_name_kor'],
    '평균학습시간': ['평균 시간', 'AvgTime', 'avg_learning_time', 'avg_time'],
    '완료률': ['완료율', 'CompletionRate', 'completion_rate'],
    # 검색어
    '검색어': ['키워드', 'Keyword', 'keyword', 'search_term', 'key_word'],
    '검색횟수': ['검색수', 'SearchCount', '검색 건수', 'search_count', 'count'],
    # 영역 현황
    '영역명': ['영역', '분야', 'area', 'area_name', '세부과정명'],
    '이수인원': ['이수 인원', 'CompletionCount', 'completion_count', '네트웍스'],
    '인증인원': ['인증 인원', 'CertificationCount', 'certification_count'],
    '도전중인원': ['도전 인원', '챌린지 인원', 'in_progress_count', 'challenge_count'],
    '이수율': ['CompletionRate', '이수 비율', 'completion_rate'],
    # 개인/배지/카드
    '개인ID': ['사번', 'EMPID', '사원번호', 'ID', 'person_id', 'employee_id', 'user_id', '개인 ID'],
    'BadgeID': ['배지ID', '배지 아이디', 'badge_id'],
    'Badge명': ['배지명', 'BadgeName', 'badge_name', '뱃지명'],
    # 시간(분) 단위 컬럼도 학습시간으로 매핑
    '학습시간': ['시간', '학습 시간', 'LearningTime', 'learning_time', 'total_learning_time', 'time', 'learn_time', '학습시간(분)']
}

def normalize_columns(df: pd.DataFrame, expected_columns: list[str]) -> pd.DataFrame:
    """별칭을 활용해 컬럼명을 표준화하고, 존재하는 최소 컬럼만 유지"""
    if df is None or df.empty:
        return df
    col_map = {}
    # 소문자 비교 용 보조 맵
    lower_to_orig = {str(c).strip(): c for c in df.columns}
    lower_existing = {str(c).strip().lower(): c for c in df.columns}
    for std_col, aliases in COLUMN_ALIASES.items():
            # 이미 표준 컬럼이 존재하면 스킵
        if std_col in df.columns:
            continue
        for alias in aliases:
            # 정확 일치 우선
            if alias in df.columns:
                col_map[alias] = std_col
                break
            # 소문자 비교(스네이크케이스 등)
            alias_l = str(alias).lower()
            if alias_l in lower_existing:
                col_map[lower_existing[alias_l]] = std_col
                break
    if col_map:
        df = df.rename(columns=col_map)
    # 공백/양끝 공백 정리
    df.columns = [str(c).strip() for c in df.columns]
    # 매핑 결과를 사용자에게 안내(디버깅/가이드)
    if col_map:
        try:
            st.caption("컬럼 자동 매핑: " + ", ".join([f"{k} → {v}" for k, v in col_map.items()]))
        except Exception:
            pass
    return df

def render_file_upload_button():
    """사이드바에 파일 업로드 버튼만 표시"""
    if st.sidebar.button("📁 파일 업로드", use_container_width=True, type="primary", key="sidebar_upload_btn"):
        st.session_state['show_upload'] = True
        st.session_state['current_page'] = None  # 업로드 화면으로 이동
        # 즉시 rerun을 위해 설정
        st.rerun()

def render_file_upload_main():
    """메인 화면에 파일 업로드 UI 표시"""
    st.header("📁 파일 업로드")
    st.caption("모든 데이터 파일을 업로드하세요")
    st.markdown("---")
    
    uploaded_files = {}
    
    # 파일 타입을 그룹화하여 표시 (더 깔끔하게)
    file_groups = {
        "기본 데이터": [
            'annual_learning', 'monthly_learning', 'category_learning'
        ],
        "콘텐츠 데이터": [
            'popular_cards', 'search_keywords'
        ],
        "Raw 데이터": [
            'individual_raw', 'card_raw', 'badge_raw', 'individual_full_raw'
        ]
    }
    
    for group_name, file_keys in file_groups.items():
        st.subheader(group_name)
        
        cols = st.columns(3)
        col_idx = 0
        
        for file_key in file_keys:
            if file_key not in FILE_TYPES:
                continue
                
            file_info = FILE_TYPES[file_key]
            current_col = cols[col_idx % 3]
            
            with current_col:
                st.markdown(f"**{file_info['name']}**")
                st.caption(file_info['description'])
                if 'expected_filename' in file_info:
                    st.caption(f"권장 파일명: {file_info['expected_filename']}")
                
                uploaded_file = st.file_uploader(
                    f"{file_info['name']} 파일",
                    type=['xlsx', 'xls', 'csv'],
                    key=f"upload_{file_key}",
                    help=f"필수 컬럼: {', '.join(file_info['required_columns'])}"
                )
                
                if uploaded_file is not None:
                    uploaded_files[file_key] = {
                        'file': uploaded_file,
                        'info': file_info
                    }
                    st.success(f"✓ 업로드 완료")
                
                col_idx += 1
        
        st.markdown("---")
    
    # 파일 데이터 로드 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if uploaded_files:
            if st.button("📥 파일 데이터 로드", type="primary", use_container_width=True):
                save_to_session(uploaded_files)
                # 업로드 후 자동으로 홈으로 이동하지 않음 (요청 반영)
                # 현재 화면 유지, 성공 메시지만 표기
                st.success("파일 로드 완료! 좌측 '📈 리포트 조회'에서 결과를 확인하세요.")
        else:
            st.info("파일을 업로드한 후 '파일 데이터 로드' 버튼을 클릭하세요")
    
    # 닫기 버튼 (선택적, 탭으로도 이동 가능)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← 홈으로 돌아가기", use_container_width=True):
            st.session_state['show_upload'] = False
            st.rerun()
    
    return uploaded_files

def render_file_upload_section():
    """파일 업로드 섹션 렌더링 (사이드바 버튼만)"""
    render_file_upload_button()
    return {}

def load_uploaded_file(uploaded_file, file_key):
    """업로드된 파일 로드"""
    try:
        # File-like object 또는 경로 처리
        if hasattr(uploaded_file, 'read'):
            # 일반적인 업로드 파일
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif hasattr(uploaded_file, 'path'):
            # 파일 경로를 가진 객체 (샘플 데이터용)
            if uploaded_file.path.endswith('.csv'):
                df = pd.read_csv(uploaded_file.path)
            else:
                df = pd.read_excel(uploaded_file.path, engine='openpyxl')
        elif isinstance(uploaded_file, str):
            # 직접 경로 문자열인 경우
            if uploaded_file.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            # DataFrame인 경우 그대로 반환
            if isinstance(uploaded_file, pd.DataFrame):
                return uploaded_file
            else:
                raise ValueError(f"지원하지 않는 파일 타입: {type(uploaded_file)}")
        
        return df
    except Exception as e:
        st.error(f"파일 로드 중 오류 발생: {str(e)}")
        return None

def validate_file_structure(df, required_columns):
    """파일 구조 검증(완화 검증 + 컬럼 자동 매핑)"""
    if df is None or df.empty:
        return False, "파일이 비어있습니다."
    # 우선 표준화 시도
    df_norm = normalize_columns(df, required_columns)
    missing_columns = [col for col in required_columns if col not in df_norm.columns]
    if missing_columns:
        return False, f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}"
    return True, "검증 완료"

def save_to_session(uploaded_files):
    """업로드된 파일들을 세션에 저장"""
    if 'uploaded_data' not in st.session_state:
        st.session_state.uploaded_data = {}
    
    for file_key, file_data in uploaded_files.items():
        df = load_uploaded_file(file_data['file'], file_key)
        if df is not None:
            original_columns = list(df.columns)
            # 컬럼 표준화 후 검증
            df_norm = normalize_columns(df, file_data['info']['required_columns'])
            is_valid, message = validate_file_structure(df_norm, file_data['info']['required_columns'])
            if is_valid:
                # 1) 학습시간(분) → 학습시간(시간) 변환
                try:
                    if '학습시간' in df_norm.columns and any(c == '학습시간(분)' for c in original_columns):
                        df_norm['학습시간'] = pd.to_numeric(df_norm['학습시간'], errors='coerce').fillna(0) / 60.0
                except Exception:
                    pass

                # 2) base_yearmonth에서 월 값 추출(정규화 후 컬럼은 '월')
                try:
                    if '월' in df_norm.columns:
                        # 12보다 큰 값이면 yyyymm 형태라고 가정 → 뒤 2자리 사용
                        max_val = pd.to_numeric(df_norm['월'], errors='coerce').max()
                        if pd.notna(max_val) and max_val > 12:
                            df_norm['월'] = pd.to_numeric(df_norm['월'], errors='coerce').astype('Int64')
                            df_norm['월'] = df_norm['월'].astype(str).str[-2:]
                            df_norm['월'] = pd.to_numeric(df_norm['월'], errors='coerce').astype('Int64')
                except Exception:
                    pass

                st.session_state.uploaded_data[file_key] = df_norm
                st.session_state.uploaded_data[f"{file_key}_info"] = file_data['info']
            else:
                st.warning(f"{file_data['info']['name']}: {message}")

