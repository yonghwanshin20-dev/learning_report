"""
Google Gemini AI 인사이트 생성 모듈
"""

import streamlit as st
from google import genai
from google.genai import types
import os

def get_gemini_client():
    """Gemini 클라이언트 초기화"""
    # 우선순위: Streamlit secrets → 환경변수(폴백)
    api_key = None
    try:
        api_key = st.secrets.get('GEMINI_API_KEY', None)
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def generate_chart_insight(client, chart_description, stats_data=None):
    """
    차트/그래프 인사이트 생성
    
    Args:
        client: Gemini 클라이언트
        chart_description: 차트 설명 텍스트
        stats_data: 통계 데이터 (딕셔너리 또는 문자열)
    """
    if client is None:
        return None
    
    try:
        system_instruction = (
            "당신은 전문적인 데이터 분석가입니다. "
            "학습 데이터를 분석하여 명확하고 실행 가능한 인사이트를 제공해야 합니다. "
            "한국어로 작성하며, 수치에는 단위를 포함하고, 핵심 트렌드와 패턴을 명확히 설명하세요."
        )
        
        prompt = f"""
다음은 학습 데이터 분석 결과입니다:

{chart_description}

"""
        
        if stats_data:
            if isinstance(stats_data, dict):
                stats_text = "\n".join([f"- {k}: {v}" for k, v in stats_data.items()])
            else:
                stats_text = str(stats_data)
            
            prompt += f"""
통계 데이터:
{stats_text}

"""
        
        prompt += """
위 데이터를 바탕으로 다음을 포함한 분석 인사이트를 작성해주세요:
1. 주요 트렌드 및 패턴 요약
2. 눈에 띄는 특징이나 이상치
3. 비즈니스 관점에서의 의미
4. 실행 가능한 제안사항 (있는 경우)

간결하고 명확하게 작성해주세요.
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_instruction}\n\n{prompt}",
            config=types.GenerateContentConfig(
                max_output_tokens=2000,
                temperature=0.7
            )
        )
        
        # 텍스트 추출
        insight_text = getattr(response, 'text', None)
        if not insight_text:
            try:
                insight_text = response.candidates[0].content.parts[0].text
            except Exception:
                insight_text = "인사이트 생성에 실패했습니다."
        
        return insight_text
    
    except Exception as e:
        st.error(f"Gemini API 호출 중 오류: {str(e)}")
        return None

def generate_eda_insight(client, analysis_type, stats_data):
    """
    EDA 분석 인사이트 생성 - 상세한 탐색적 데이터 분석
    
    Args:
        client: Gemini 클라이언트
        analysis_type: 분석 타입 ('조직별', '직책별', '개인별', '변화군별')
        stats_data: 통계 데이터 (DataFrame 또는 문자열)
    """
    if client is None:
        return None
    
    try:
        system_instruction = (
            "당신은 전문적인 데이터 분석가입니다. "
            "탐색적 데이터 분석(EDA) 결과를 바탕으로 조직의 학습 특징을 깊이 있게 분석하고 실행 가능한 인사이트를 제공해야 합니다. "
            "각 그룹의 특징, 학습 패턴, 그룹 간 차이점을 구체적으로 설명하고, 어떤 사람들이 어떤 학습을 많이 하는지 분석하세요."
        )
        
        analysis_prompts = {
            '조직별': """조직별 학습 특징을 상세히 분석하세요:
- 각 조직(사업부)의 학습 패턴과 특징
- 어떤 조직이 어떤 종류의 학습을 선호하는지
- 조직 간 학습 문화의 차이점
- 조직별 학습자들의 특성 (직책 분포, 연령대, 직무 등)
- 학습 효과가 높은 조직의 특징
- 조직 간 학습 격차와 그 원인""",
            
            '직책별': """직책별 학습 특징을 상세히 분석하세요 (임원, 팀장, 구성원 순서로):
- 각 직책별 학습 시간과 패턴
- 임원/팀장/구성원의 학습 목적과 특성 차이
- 리더십 학습 문화와 그 효과
- 각 직책별 선호하는 학습 콘텐츠 유형
- 직책별 Badge 취득률과 학습 완료률
- 고성과 학습자의 직책별 특징
- 리더의 학습이 조직에 미치는 영향""",
            
            '개인별': """개인별 학습 분포를 상세히 분석하세요:
- 저학습자와 고학습자의 명확한 특징 차이
- 고학습자의 학습 패턴과 동기
- 저학습자의 학습 장벽과 특성
- 학습 시간 분포의 의미와 비즈니스 인사이트
- 개인별 학습 성과의 영향 요인
- 학습 활성화를 위한 개선 방안""",
            
            '변화군별': """학습시간 변화군을 상세히 분석하세요:
- 각 변화군(지속 저학습군, 지속 고학습군, 상승군, 하락군)의 특징
- 변화군별 학습자들의 속성 (직책, 연령대, 직무 등)
- 변화 패턴의 원인과 의미
- 변화군별 선호하는 학습 콘텐츠
- 상승군의 성공 요인
- 하락군의 학습 저하 원인 추론
- 변화군별 맞춤형 학습 전략"""
        }
        
        # 통계 데이터를 문자열로 변환
        if isinstance(stats_data, pd.DataFrame):
            stats_text = stats_data.to_string(index=False)
        else:
            stats_text = str(stats_data)
        
        prompt = f"""
{analysis_type} 학습 데이터 탐색적 데이터 분석(EDA) 결과:

{stats_text}

{analysis_prompts.get(analysis_type, '')}

위 데이터를 바탕으로 다음을 포함한 매우 상세하고 구체적인 분석을 작성해주세요:
1. **각 그룹의 학습 특징 요약**: 수치와 함께 구체적으로 설명
2. **그룹 간 차이점 및 비교 분석**: 어떤 그룹이 어떤 특징을 보이는지
3. **학습 패턴 분석**: 어떤 학습을 많이 하고, 어떤 사람들이 학습에 적극적인지
4. **비즈니스 인사이트**: 데이터가 시사하는 의미와 조직에 미치는 영향
5. **개선 방안 제안**: 구체적이고 실행 가능한 개선 방안

각 섹션을 상세하고 구체적으로 작성하며, 수치와 데이터를 활용하여 설명하세요.
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_instruction}\n\n{prompt}",
            config=types.GenerateContentConfig(
                max_output_tokens=4000,
                temperature=0.7
            )
        )
        
        insight_text = getattr(response, 'text', None)
        if not insight_text:
            try:
                insight_text = response.candidates[0].content.parts[0].text
            except Exception:
                insight_text = "인사이트 생성에 실패했습니다."
        
        return insight_text
    
    except Exception as e:
        st.error(f"Gemini API 호출 중 오류: {str(e)}")
        return None

