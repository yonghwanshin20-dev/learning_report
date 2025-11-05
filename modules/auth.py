"""
인증 모듈
로그인 및 세션 관리 기능
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

def load_config():
    """설정 파일 로드"""
    config_path = 'config.yaml'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.load(file, Loader=SafeLoader)
    else:
        st.error("설정 파일(config.yaml)을 찾을 수 없습니다.")
        return None

def initialize_authentication():
    """인증 시스템 초기화"""
    config = load_config()
    if not config:
        return None
    
    # preauthorized 파라미터는 최신 버전에서 제거됨
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    return authenticator

def check_authentication():
    """인증 상태 확인"""
    # 세션에 이미 인증 정보가 있는지 확인
    if 'authentication_status' in st.session_state and st.session_state.get('authentication_status') == True:
        # 이미 로그인된 상태
        authenticator = st.session_state.get('authenticator')
        if authenticator:
            # 로그아웃 버튼 표시
            with st.sidebar:
                name = st.session_state.get('name', '사용자')
                st.write(f'환영합니다, *{name}*님')
                authenticator.logout('로그아웃', 'sidebar')
        return True
    
    # 인증 시스템 초기화
    if 'authenticator' not in st.session_state:
        st.session_state.authenticator = initialize_authentication()
    
    authenticator = st.session_state.authenticator
    if authenticator is None:
        st.error("인증 시스템 초기화에 실패했습니다. config.yaml 파일을 확인하세요.")
        return False
    
    try:
        # 로그인 페이지 표시
        login_result = authenticator.login()
        
        # login()이 None을 반환하는 경우 처리
        if login_result is None:
            # 로그인 폼만 표시되고 아직 인증되지 않은 상태
            return False
        
        # 튜플 언팩
        name, authentication_status, username = login_result
        
        if authentication_status == False:
            st.error('사용자명 또는 비밀번호가 올바르지 않습니다.')
            st.session_state['authentication_status'] = False
            return False
        elif authentication_status == None:
            st.warning('사용자명과 비밀번호를 입력하세요.')
            return False
        elif authentication_status:
            # 로그인 성공 - 세션 상태에 저장
            st.session_state['authentication_status'] = True
            st.session_state['name'] = name
            st.session_state['username'] = username
            
            # 로그아웃 버튼 (사이드바)
            with st.sidebar:
                st.write(f'환영합니다, *{name}*님')
                authenticator.logout('로그아웃', 'sidebar')
            
            # 페이지 새로고침을 위해 rerun (한 번만)
            if 'login_success_rerun' not in st.session_state:
                st.session_state['login_success_rerun'] = True
                st.rerun()
            
            return True
        
        return False
    
    except TypeError as e:
        # 언팩 에러 처리 (login()이 다른 형태로 반환하는 경우)
        st.error(f"인증 오류가 발생했습니다: {str(e)}")
        st.info("설정 파일(config.yaml)을 확인하거나 애플리케이션을 재시작해보세요.")
        return False
    except Exception as e:
        st.error(f"인증 시스템 오류: {str(e)}")
        return False

