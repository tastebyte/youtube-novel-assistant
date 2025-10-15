"""
유튜브소설어시스트 - 메인 애플리케이션
Streamlit 기반 소설 제작 도구
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json
import pandas as pd
import time

# 환경 변수 로드
load_dotenv()

# 프로젝트 모듈 import
from src.models import Novel, Character, Scene, generate_uuid
from src.data_manager import DataManager
from src.utils import get_api_key


def initialize_session_state():
    """세션 상태 초기화"""
    if 'current_novel_id' not in st.session_state:
        st.session_state.current_novel_id = None
    if 'current_scene_id' not in st.session_state:
        st.session_state.current_scene_id = None
    if 'novels' not in st.session_state:
        st.session_state.novels = {}
    if 'novel_created' not in st.session_state:
        st.session_state.novel_created = False
    if 'created_novel_title' not in st.session_state:
        st.session_state.created_novel_title = ""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    if 'api_usage' not in st.session_state:
        st.session_state.api_usage = {}
    if 'cumulative_api_usage' not in st.session_state:
        st.session_state.cumulative_api_usage = load_cumulative_api_usage()
    if 'last_usage_save_time' not in st.session_state:
        st.session_state.last_usage_save_time = time.time()
    if 'api_key_status' not in st.session_state:
        # 앱 시작 시 API 키 유효성 검사 (세션당 1회)
        st.session_state.api_key_status = check_api_key_validity()

    
    # 기존 소설 목록 로드
    if not st.session_state.novels:
        st.session_state.novels = st.session_state.data_manager.load_novels()
    
    # 5분마다 누적 사용량 저장
    if time.time() - st.session_state.last_usage_save_time > 300:
        update_and_save_cumulative_usage()


@st.cache_data(show_spinner=False)
def check_api_key_validity() -> dict:
    """앱 시작 시 API 키 유효성을 검사하고 결과를 반환합니다."""
    from src.api_clients import GeminiClient
    
    api_key = get_api_key('gemini')
    if not api_key:
        return {"valid": False, "message": "API 키가 설정되지 않았습니다."}

    try:
        client = GeminiClient()
        if client.test_api_connection():
            return {"valid": True, "message": "API 키가 유효합니다."}
        return {"valid": False, "message": "API 키가 유효하지 않거나 연결에 실패했습니다."}
    except Exception as e:
        return {"valid": False, "message": f"API 검증 중 오류 발생: {e}"}


def main():
    """메인 애플리케이션 진입점"""
    st.set_page_config(
        page_title="유튜브소설어시스트",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 세션 상태 초기화
    initialize_session_state()
    
    # 사용자 정의 CSS 주입 (줄 간격 줄이기)
    st.markdown("""
        <style>
            /* Streamlit의 기본 블록 컨테이너 간격 줄이기 */
            div[data-testid="stVerticalBlock"] {
                gap: 0.1rem; /* 기본값 1rem에서 줄임 */
            }
            /* 헤더, 서브헤더 등의 위아래 여백 줄이기 */
            h1, h2, h3, h4, h5, h6 {
                margin-bottom: 0.1rem !important;
            }
            /* 메인 콘텐츠 영역의 위쪽 여백 줄이기 */
            div[data-testid="stBlockContainer"] {
                padding-top: 0.0rem !important; /* 기본값 5rem에서 줄임 */
            }
            /* st.metric 폰트 크기 줄이기 */
            div[data-testid="stMetricLabel"] {
                font-size: 14px !important; /* 라벨 폰트 크기 */
            }
            div[data-testid="stMetricValue"] {
                font-size: 20px !important; /* 값 폰트 크기 */
                font-weight: bold !important; /* 값 굵게 만들기 */
            }
            /* 상세 화면의 메뉴 버튼 폰트 크기 지정 */
            button[data-testid="stButton"] > div > p {
                font-size: 18px !important;
            }
            
            /* --- 탭 스타일 변경 (박스 형태) --- */
            /* 탭 컨테이너 전체 - 아래쪽 선 제거 */
            div[data-testid="stTabs"] {
                border-bottom: none;
                margin-bottom: 1rem; /* 탭과 내용 사이 간격 */
            }
            
            /* 각 탭 버튼 (선택되지 않았을 때) */
            button[data-testid="stTab"] {
                font-size: 18px; /* 폰트 크기 키움 */
                font-weight: 600;
                color: #4f4f4f; /* 약간 진한 회색 */
                background-color: #f0f2f6; /* 밝은 회색 배경 */
                border: 1px solid #dcdcdc; /* 테두리 추가 */
                border-radius: 8px; /* 모서리 둥글게 */
                padding: 12px 20px; /* 내부 여백 추가로 버튼 크기 키움 */
                margin-right: 8px; /* 탭 간 간격 */
                transition: all 0.2s; /* 부드러운 전환 효과 */
            }

            /* 선택된 탭 버튼 */
            button[data-testid="stTab"][aria-selected="true"] {
                font-weight: 700; /* 굵게 */
                color: #ffffff; /* 흰색 글자 */
                background-color: #4A90E2; /* 파란색 배경 */
                border: 1px solid #4A90E2; /* 파란색 테두리 */
            }

            /* 탭 위에 마우스 올렸을 때 (선택되지 않은 탭) */
            button[data-testid="stTab"]:not([aria-selected="true"]):hover {
                background-color: #e6eaf0;
                color: #2c2c2c;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 메인 타이틀 (50% 크기)
    st.markdown('<h2 style="font-size: 1.5rem; color: #4A90E2;">📚 유튜브소설어시스트</h2>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 사이드바
    render_sidebar()
    
    # 메인 콘텐츠
    render_main_content()


def render_sidebar():
    """사이드바 렌더링"""
    # API 키 상태 표시
    api_status = st.session_state.get('api_key_status', {})
    if api_status.get('valid'):
        st.sidebar.success("✅ API 키가 활성화되었습니다.", icon="🔑")
    else:
        st.sidebar.error(f"❌ {api_status.get('message', 'API 키 확인 필요')}", icon="🔑")
        if st.sidebar.button("문제 해결 가이드 보기"):
            st.session_state.page = "troubleshoot"
            st.rerun()

    with st.sidebar:
        st.header("메뉴")
        
        # 소설 관리
        st.subheader("소설 관리")
        if st.button("새 소설 생성", use_container_width=True):
            st.session_state.page = "create_novel"
            st.rerun()
        
        # 소설 목록
        st.subheader("소설 목록")
        novels = st.session_state.novels
        
        if novels:
            # 생성된 날짜의 역순으로 소설 정렬
            sorted_novels = sorted(novels.items(), key=lambda item: item[1].created_at, reverse=True)

            for novel_id, novel in sorted_novels:
                # 소설 카드
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if st.button(
                            f"📖 {novel.title}",
                            key=f"novel_{novel_id}",
                            use_container_width=True,
                            help=f"생성일: {novel.created_at.strftime('%Y-%m-%d %H:%M')}"
                        ):
                            st.session_state.current_novel_id = novel_id
                            st.session_state.page = "novel_detail"
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_{novel_id}", help="삭제"):
                            # 삭제 확인
                            if st.session_state.get(f'confirm_delete_{novel_id}', False):
                                # 실제 삭제
                                st.session_state.data_manager.delete_novel(novel_id)
                                del st.session_state.novels[novel_id]
                                st.success(f"'{novel.title}' 소설이 삭제되었습니다.")
                                st.session_state[f'confirm_delete_{novel_id}'] = False
                                st.rerun()
                            else:
                                # 삭제 확인 요청
                                st.session_state[f'confirm_delete_{novel_id}'] = True
                                st.warning(f"'{novel.title}' 삭제하시겠습니까? 다시 🗑️ 버튼을 클릭하세요.")
                                st.rerun()
        else:
            st.info("소설이 없습니다. 새 소설을 생성해주세요.")
        
        # API 사용량 표시
        st.markdown("---")
        with st.expander("📊 API 사용량", expanded=True):
            render_api_usage_stats()


def render_api_usage_stats():
    """API 사용량 통계 및 차트 렌더링"""
    session_usage = st.session_state.get('api_usage', {})    

    if not session_usage:
        st.info("현재 세션의 API 사용 기록이 없습니다.")
        return

    # 데이터 준비
    services = sorted(session_usage.keys())
    data = []
    for service in services:
        s_usage = session_usage.get(service, {})

        data.append({
            "Service": service.upper(),
            "요청 수": s_usage.get('total_requests', 0),
            "토큰 사용량": s_usage.get('total_tokens', 0),
        })

    if not data:
        st.info("현재 세션의 API 사용 기록이 없습니다.")
        return

    df = pd.DataFrame(data)

    tab1, tab2 = st.tabs(["📈 현재 세션 요청 수", "🪙 현재 세션 토큰 사용량"])

    with tab1:
        for _, row in df.iterrows():
            st.metric(
                label=f"{row['Service']} 요청",
                value=f"{row['요청 수']:,} 회"
            )

    with tab2:
        for _, row in df.iterrows():
            st.metric(
                label=f"{row['Service']} 토큰",
                value=f"{row['토큰 사용량']:,}"
            )

        st.caption(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")


def render_main_content():
    """메인 콘텐츠 렌더링"""
    # 페이지 상태에 따른 콘텐츠 표시
    page = st.session_state.get('page', 'welcome')
    
    if page == 'welcome':
        render_welcome_screen()
    elif page == 'create_novel':
        render_create_novel_screen()
    elif page == 'novel_detail':
        render_novel_detail_screen()
    elif page == 'troubleshoot':
        render_troubleshoot_screen()
    else:
        render_welcome_screen()


def render_welcome_screen():
    """환영 화면"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ## 환영합니다! 👋
        
        유튜브소설어시스트는 AI를 활용하여 소설 제작을 도와주는 도구입니다.
        
        ### 주요 기능:
        - 📝 **대본 입력**: 소설의 전체 대본을 입력
        - 👥 **등장인물 자동 추출**: AI가 대본에서 등장인물을 자동으로 찾아냄
        - 🎨 **캐릭터 이미지 생성**: 각 등장인물의 일관된 이미지 생성
        - 🎬 **장면 자동 분리**: 대본을 개별 장면으로 자동 분할
        - 🖼️ **장면 이미지 생성**: 각 장면에 맞는 이미지 자동 생성
        - 💾 **저장 및 관리**: 모든 데이터를 체계적으로 저장하고 관리
        
        ### 시작하기:
        왼쪽 사이드바에서 **"새 소설 생성"** 버튼을 클릭하여 시작하세요!
        """)

def render_troubleshoot_screen():
    """문제 해결 가이드 화면"""
    st.header("🔧 문제 해결 가이드: API 키 설정")
    st.error("AI 기능을 사용하려면 유효한 Gemini API 키가 필요합니다.")
    
    st.markdown("""
    API 키 연결에 실패하는 경우 아래 사항들을 확인해주세요.

    #### 1. API 키가 올바르게 설정되었나요?
    프로젝트 폴더의 `.streamlit/secrets.toml` 파일에 API 키가 정확히 입력되었는지 확인하세요.
    ```toml
    # .streamlit/secrets.toml
    GEMINI_API_KEY = "여기에_실제_API_키를_입력하세요"
    ```

    #### 2. API 키가 유효한가요?
    - Google AI Studio에 방문하여 API 키가 활성화되어 있는지 확인하세요.
    - API 키의 사용량 한도(할당량)가 초과되지 않았는지 확인하세요.
    - 결제 정보가 올바르게 등록되어 있는지 확인하세요.
    """)

def render_create_novel_screen():
    """새 소설 생성 화면"""
    st.header("새 소설 생성")
    
    # 소설 생성 완료 메시지 표시
    if st.session_state.novel_created:
        st.success(f"🎉 '{st.session_state.created_novel_title}' 소설이 성공적으로 생성되었습니다!")
        st.info("💡 이제 왼쪽 사이드바에서 생성된 소설을 확인할 수 있습니다.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📖 소설 상세보기", use_container_width=True):
                st.session_state.page = 'novel_detail'
                st.session_state.novel_created = False
                st.rerun()
        with col2:
            if st.button("➕ 새 소설 더 만들기", use_container_width=True):
                st.session_state.novel_created = False
                st.session_state.created_novel_title = ""
                st.rerun()
        with col3:
            if st.button("🏠 메인으로 돌아가기", use_container_width=True):
                st.session_state.page = 'welcome'
                st.session_state.novel_created = False
                st.session_state.created_novel_title = ""
                st.rerun()
        return
    
    # 소설 생성 폼
    with st.form("create_novel_form"):
        st.subheader("기본 정보")
        
        title = st.text_input("소설 제목", placeholder="예: 도시의 밤")
        
        st.subheader("전체 대본")
        script = st.text_area(
            "대본 내용",
            height=400,
            placeholder="""예시:
            
제1장 - 만남
주인공 김민수는 늦은 밤 편의점에서 아르바이트를 하고 있었다.
김민수: "또 다른 평범한 밤이군..."

그때 신비로운 여자 이하나가 들어왔다.
이하나: "안녕하세요. 이상한 질문일 수도 있지만... 시간을 되돌릴 수 있다면 어떻게 하시겠어요?"

제2장 - 비밀
다음 날, 민수는 하나를 다시 만났다...
            """)
        
        submitted = st.form_submit_button("📝 소설 생성", use_container_width=True)
        
        if submitted:
            if not title.strip():
                st.error("❌ 소설 제목을 입력해주세요.")
            elif not script.strip():
                st.error("❌ 대본 내용을 입력해주세요.")
            else:
                # 소설 생성
                with st.spinner("📚 소설을 생성하고 있습니다..."):
                    try:
                        # 새 소설 객체 생성
                        novel = Novel(
                            id=generate_uuid(),
                            title=title.strip(),
                            description="",
                            script=script.strip(),
                            created_at=datetime.now(),
                            characters={},
                            scenes={}
                        )
                        
                        # 데이터 저장
                        data_manager = st.session_state.data_manager
                        if data_manager.save_novel(novel):
                            # 메타데이터 업데이트
                            st.session_state.novels[novel.id] = novel
                            data_manager.save_novels(st.session_state.novels)
                            
                            # 성공 상태 저장
                            st.session_state.novel_created = True
                            st.session_state.created_novel_title = title
                            st.session_state.current_novel_id = novel.id
                            st.rerun()
                        else:
                            st.error("❌ 소설 저장에 실패했습니다.")
                            
                    except Exception as e:
                        st.error(f"❌ 소설 생성 중 오류 발생: {str(e)}")
    
    # 메인으로 돌아가기 버튼
    st.markdown("---")
    if st.button("← 메인으로 돌아가기", key="back_to_main"):
        st.session_state.page = 'welcome'
        st.rerun()


def render_novel_detail_screen():
    """소설 상세 화면"""
    if not st.session_state.current_novel_id:
        st.error("선택된 소설이 없습니다.")
        return
    
    novel_id = st.session_state.current_novel_id
    novel = st.session_state.novels.get(novel_id)
    
    if not novel:
        st.error("소설을 찾을 수 없습니다.")
        return
    
    # 소설 헤더
    edit_title_key = f"edit_title_{novel.id}"
    if st.session_state.get(edit_title_key, False):
        # 제목 편집 모드
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            new_title = st.text_input("새 소설 제목", value=novel.title, key=f"new_title_{novel.id}", label_visibility="collapsed")
        with col2:
            if st.button("💾 저장", key=f"save_title_{novel.id}", use_container_width=True):
                if new_title.strip():
                    old_title = novel.title
                    novel.title = new_title.strip()
                    
                    data_manager = st.session_state.data_manager
                    if data_manager.save_novel(novel) and data_manager.save_novels(st.session_state.novels):
                        st.success(f"소설 제목이 '{old_title}'에서 '{novel.title}'(으)로 변경되었습니다.")
                        st.session_state[edit_title_key] = False
                        st.rerun()
                    else:
                        novel.title = old_title # 실패 시 원상 복구
                        st.error("제목 저장에 실패했습니다.")
                else:
                    st.warning("제목은 비워둘 수 없습니다.")
        with col3:
            if st.button("❌ 취소", key=f"cancel_title_{novel.id}", use_container_width=True):
                st.session_state[edit_title_key] = False
                st.rerun()
    else:
        # 제목 표시 모드
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.subheader(f"📖 {novel.title}", anchor=False)
        with col2:
            if st.button("✏️", key=f"show_edit_title_{novel.id}", use_container_width=True):
                st.session_state[edit_title_key] = True
                st.rerun()
    
    # 소설 정보
    st.markdown("---")
    
    # 기본 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("장", f"{novel.chapter_count}개")
    with col2:
        st.metric("등장인물", f"{novel.character_count}명")
    with col3:
        st.metric("장면", f"{novel.scene_count}개")
    with col4:
        st.metric("생성일", novel.created_at.strftime("%Y-%m-%d"))
    
    # 탭으로 구분
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 대본", " 등장인물", " 장 관리", "🎬 장면", "🤖 AI 분석"])
    
    with tab1:
        st.subheader("전체 대본")
        
        if novel.script:
            # 편집 취소 플래그 확인
            cancel_key = f"cancel_edit_{novel.id}"
            if cancel_key in st.session_state and st.session_state[cancel_key]:
                # 취소 플래그 제거하고 편집 모드 비활성화
                del st.session_state[cancel_key]
                if f"edit_script_{novel.id}" in st.session_state:
                    del st.session_state[f"edit_script_{novel.id}"]
                st.rerun()
            
            # 대본 편집 모드 토글
            edit_mode = st.checkbox("📝 대본 편집 모드", key=f"edit_script_{novel.id}")
            
            if edit_mode:
                # 저장 완료 후 편집 모드 종료 확인
                saved_key = f"saved_script_{novel.id}"
                if saved_key in st.session_state and st.session_state[saved_key]:
                    del st.session_state[saved_key]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ 편집 계속하기", use_container_width=True):
                            st.rerun()
                    with col2:
                        if st.button("🚪 편집 모드 종료", use_container_width=True):
                            st.session_state[f"cancel_edit_{novel.id}"] = True
                            st.rerun()
                    return
                
                # 전처리된 대본이 있는지 확인
                processed_key = f"processed_script_{novel.id}"
                if processed_key in st.session_state:
                    script_value = st.session_state[processed_key]
                    # 전처리 완료 메시지 표시
                    st.success(f"✅ 전처리가 완료되었습니다! (길이: {len(script_value):,} 문자)")
                else:
                    script_value = novel.script
                
                # 편집 가능한 대본
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    new_script = st.text_area(
                        "대본 내용 (편집 가능)", 
                        value=script_value, 
                        height=400,
                        key=f"script_editor_{novel.id}"
                    )
                
                with col2:
                    st.markdown("### 대본 도구")
                    
                    # 대본 전처리 버튼들
                    if st.button("🧹 공백 정리", help="불필요한 공백과 줄바꿈 정리", key=f"clean_ws_{novel.id}"):
                        with st.spinner("공백을 정리하고 있습니다..."):
                            cleaned_script = preprocess_script_whitespace(new_script)
                            st.session_state[f"processed_script_{novel.id}"] = cleaned_script
                            st.success(f"공백 정리 완료! {len(new_script)} → {len(cleaned_script)} 문자")
                        st.rerun()
                    
                    if st.button("📖 문단 정리", help="문단 구분을 명확하게 정리", key=f"clean_para_{novel.id}"):
                        with st.spinner("문단을 정리하고 있습니다..."):
                            formatted_script = preprocess_script_paragraphs(new_script)
                            st.session_state[f"processed_script_{novel.id}"] = formatted_script
                            st.success(f"문단 정리 완료! {len(new_script)} → {len(formatted_script)} 문자")
                        st.rerun()
                    
                    if st.button("💬 대사 정리", help="대사 형식을 표준화", key=f"clean_dial_{novel.id}"):
                        with st.spinner("대사를 정리하고 있습니다..."):
                            dialogue_script = preprocess_script_dialogue(new_script)
                            st.session_state[f"processed_script_{novel.id}"] = dialogue_script
                            st.success(f"대사 정리 완료! {len(new_script)} → {len(dialogue_script)} 문자")
                        st.rerun()
                    
                    if st.button("🔧 특수문자 정리", help="불필요한 특수문자 제거 (. , ! ? ' ` 제외)", key=f"clean_special_{novel.id}"):
                        with st.spinner("특수문자를 정리하고 있습니다..."):
                            cleaned_script = preprocess_script_special_chars(new_script)
                            st.session_state[f"processed_script_{novel.id}"] = cleaned_script
                            st.success(f"특수문자 정리 완료! {len(new_script)} → {len(cleaned_script)} 문자")
                        st.rerun()
                    
                    if st.button("📜 중복 줄바꿈 제거", help="연속된 여러 줄바꿈을 하나로 합칩니다.", key=f"clean_newlines_{novel.id}"):
                        with st.spinner("중복 줄바꿈을 제거하고 있습니다..."):
                            cleaned_script = preprocess_script_remove_duplicate_newlines(new_script)
                            st.session_state[f"processed_script_{novel.id}"] = cleaned_script
                            st.success(f"중복 줄바꿈 제거 완료! {len(new_script)} → {len(cleaned_script)} 문자")
                        st.rerun()

                    st.markdown("---")
                    with st.expander("🔎 찾아 바꾸기"):
                        find_key = f"find_text_{novel.id}"
                        replace_key = f"replace_text_{novel.id}"
                        
                        find_text = st.text_input("찾을 단어", key=find_key)
                        replace_text = st.text_input("바꿀 단어", key=replace_key)
                        
                        # 찾을 단어가 입력되면 실시간으로 개수 표시
                        if find_text:
                            # new_script는 text_area의 현재 값을 가지고 있음
                            count = new_script.count(find_text)
                            st.info(f"'{find_text}' 단어가 현재 대본에 {count}번 있습니다.")

                        def handle_replace():
                            """찾아 바꾸기 실행 콜백 함수"""
                            # text_area의 현재 값을 가져옴
                            current_script = st.session_state.get(f"script_editor_{novel.id}", novel.script)
                            find_val = st.session_state.get(find_key, "")
                            replace_val = st.session_state.get(replace_key, "")

                            if not find_val:
                                st.warning("찾을 단어를 입력해주세요.")
                                return

                            count = current_script.count(find_val)
                            replaced_script = current_script.replace(find_val, replace_val)
                            
                            # 변경된 내용을 processed_script에 저장하여 text_area에 즉시 반영
                            st.session_state[f"processed_script_{novel.id}"] = replaced_script
                            
                            # 입력 필드 초기화
                            st.session_state[find_key] = ""
                            st.session_state[replace_key] = ""
                            st.success(f"'{find_val}' 단어를 '{replace_val}'(으)로 {count}번 바꿨습니다.")

                        st.button("🔄 바꾸기 실행", key=f"replace_button_{novel.id}", on_click=handle_replace)

                    st.markdown("---")
                    
                    # 전체 전처리 버튼
                    if st.button("🚀 전체 전처리", help="모든 전처리를 한 번에 실행", key=f"clean_all_{novel.id}"):
                        with st.spinner("전체 전처리를 실행하고 있습니다..."):
                            original_length = len(new_script)
                            
                            # 1단계: 특수문자 정리
                            step1 = preprocess_script_special_chars(new_script)
                            
                            # 2단계: 공백 정리
                            step2 = preprocess_script_whitespace(step1)
                            
                            # 3단계: 문단 정리
                            step3 = preprocess_script_paragraphs(step2)
                            
                            # 4단계: 대사 정리
                            final_script = preprocess_script_dialogue(step3)
                            
                            st.session_state[f"processed_script_{novel.id}"] = final_script
                            st.success(f"전체 전처리 완료! {original_length:,} → {len(final_script):,} 문자")
                        st.rerun()
                    
                    if st.button("📚 장으로 분리", help="대본을 장(Chapter)으로 분리하여 저장", key=f"split_chapters_{novel.id}"):
                        with st.spinner("대본을 장으로 분리하고 있습니다..."):
                            chapters = split_script_into_chapters(new_script, novel.id)
                            if chapters:
                                # 기존 장 데이터 초기화
                                novel.chapters = {}
                                
                                # 새 장 데이터 추가
                                for chapter in chapters:
                                    novel.chapters[chapter.id] = chapter
                                
                                # 저장
                                data_manager = st.session_state.data_manager
                                if data_manager.save_novel(novel):
                                    st.session_state.novels[novel.id] = novel
                                    data_manager.save_novels(st.session_state.novels)
                                    st.success(f"📚 {len(chapters)}개 장으로 분리 완료!")
                                else:
                                    st.error("❌ 장 분리 저장에 실패했습니다.")
                            else:
                                st.warning("⚠️ 장 구분자를 찾을 수 없습니다. (#1장, #2장 형식을 사용해주세요)")
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # 저장 버튼
                    if st.button("💾 대본 저장", type="primary", use_container_width=True):
                        try:
                            original_script = novel.script.strip()
                            new_script_clean = new_script.strip()
                            
                            # 변경사항 확인
                            if new_script_clean != original_script:
                                with st.spinner("대본을 저장하고 있습니다..."):
                                    # 저장 전 상태 표시
                                    st.info(f"저장 중... 원본: {len(original_script):,} 문자 → 새 버전: {len(new_script_clean):,} 문자")
                                    
                                    # 대본 업데이트
                                    novel.script = new_script_clean
                                    
                                    # 전처리 세션 상태 초기화
                                    if f"processed_script_{novel.id}" in st.session_state:
                                        del st.session_state[f"processed_script_{novel.id}"]
                                    
                                    # 데이터 저장 시도
                                    data_manager = st.session_state.data_manager
                                    save_result = data_manager.save_novel(novel)
                                    
                                    if save_result:
                                        # 메타데이터 업데이트
                                        st.session_state.novels[novel.id] = novel
                                        meta_result = data_manager.save_novels(st.session_state.novels)
                                        
                                        if meta_result:
                                            st.success(f"✅ 대본이 성공적으로 저장되었습니다! (길이: {len(novel.script):,} 문자)")
                                            
                                            # 저장된 파일 확인
                                            from src.utils import get_novel_directory
                                            novel_dir = get_novel_directory(novel.id)
                                            script_file = novel_dir / "script.txt"
                                            
                                            if script_file.exists():
                                                with open(script_file, 'r', encoding='utf-8') as f:
                                                    saved_content = f.read()
                                                st.info(f"📁 파일 저장 확인: {len(saved_content):,} 문자가 {script_file}에 저장됨")
                                            
                                            # 저장 후 편집 모드 종료 옵션
                                            st.session_state[f"saved_script_{novel.id}"] = True
                                            st.rerun()
                                        else:
                                            st.error("❌ 메타데이터 저장에 실패했습니다.")
                                    else:
                                        st.error("❌ 대본 파일 저장에 실패했습니다.")
                            else:
                                st.info("변경사항이 없습니다.")
                                
                        except Exception as e:
                            st.error(f"저장 중 오류 발생: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                    
                    # 취소 버튼
                    if st.button("❌ 편집 취소", use_container_width=True):
                        # 전처리 세션 상태 초기화
                        if f"processed_script_{novel.id}" in st.session_state:
                            del st.session_state[f"processed_script_{novel.id}"]
                        
                        # 편집 모드 종료를 위한 플래그 설정
                        st.session_state[f"cancel_edit_{novel.id}"] = True
                        st.rerun()
                
                # 대본 통계 및 저장 상태
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("총 글자수", f"{len(new_script):,}")
                with col2:
                    st.metric("줄 수", f"{len(new_script.splitlines()):,}")
                with col3:
                    word_count = len(new_script.replace('\n', ' ').split())
                    st.metric("단어 수", f"{word_count:,}")
                with col4:
                    char_count_no_space = len(new_script.replace(' ', '').replace('\n', ''))
                    st.metric("공백 제외", f"{char_count_no_space:,}")
                
                # 저장 상태 표시
                if new_script.strip() != novel.script.strip():
                    st.warning("⚠️ 변경사항이 있습니다. 저장하지 않으면 변경사항이 손실됩니다.")
                else:
                    st.success("✅ 현재 내용이 저장된 상태입니다.")
            
            else:
                # 읽기 전용 대본
                st.text_area("대본 내용 (읽기 전용)", value=novel.script, height=400, disabled=True)
                
                # 대본 통계 (읽기 모드)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("총 글자수", f"{len(novel.script):,}")
                with col2:
                    st.metric("줄 수", f"{len(novel.script.splitlines()):,}")
                with col3:
                    word_count = len(novel.script.replace('\n', ' ').split())
                    st.metric("단어 수", f"{word_count:,}")
                with col4:
                    char_count_no_space = len(novel.script.replace(' ', '').replace('\n', ''))
                    st.metric("공백 제외", f"{char_count_no_space:,}")
                
                # 저장 파일 정보 표시
                try:
                    from src.utils import get_novel_directory
                    novel_dir = get_novel_directory(novel.id)
                    script_file = novel_dir / "script.txt"
                    
                    if script_file.exists():
                        import os
                        file_size = os.path.getsize(script_file)
                        modified_time = os.path.getmtime(script_file)
                        from datetime import datetime
                        modified_str = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")
                        
                        st.info(f"📁 저장 파일: {script_file} ({file_size:,} 바이트, 수정: {modified_str})")
                    else:
                        st.warning("⚠️ 저장 파일이 존재하지 않습니다.")
                except Exception as e:
                    st.error(f"파일 정보 확인 오류: {str(e)}")
        else:
            st.info("대본이 없습니다.")
            if st.button("📝 대본 추가하기"):
                st.session_state[f"edit_script_{novel.id}"] = True
                st.rerun()
    
    with tab2: # 2. 등장인물 탭
        st.subheader("등장인물 관리")
        if novel.characters:
            # 이름순으로 정렬하여 일관된 순서 유지
            sorted_characters = sorted(novel.characters.items(), key=lambda item: item[1].name)
            for char_id, character in sorted_characters:
                with st.expander(f"👤 {character.name}"):
                    edit_desc_key = f"edit_desc_{character.id}"

                    if st.session_state.get(edit_desc_key, False):
                        # --- 설명 편집 모드 ---
                        new_description = st.text_area(
                            "설명 수정",
                            value=character.description,
                            key=f"desc_textarea_{character.id}",
                            height=150
                        )
                        
                        col1, col2, col3 = st.columns([1, 1, 5])
                        with col1:
                            if st.button("💾 저장", key=f"save_desc_{character.id}", use_container_width=True):
                                character.description = new_description
                                data_manager = st.session_state.data_manager
                                if data_manager.save_novel(novel):
                                    st.session_state.novels[novel.id] = novel
                                    data_manager.save_novels(st.session_state.novels)
                                    st.success(f"'{character.name}'의 설명이 저장되었습니다.")
                                    st.session_state[edit_desc_key] = False
                                    st.rerun()
                                else:
                                    st.error("설명 저장에 실패했습니다.")
                        with col2:
                            if st.button("❌ 취소", key=f"cancel_desc_{character.id}", use_container_width=True):
                                st.session_state[edit_desc_key] = False
                                st.rerun()
                    else:
                        # --- 설명 표시 모드 ---
                        st.write(f"**설명:** {character.description}")
                        
                        col1, col2, col_rest = st.columns([2, 2, 5])
                        with col1:
                            if st.button("✏️ 설명 수정", key=f"show_edit_desc_{character.id}", use_container_width=True):
                                st.session_state[edit_desc_key] = True
                                st.rerun()
                        with col2:
                            button_text = "🎨 이미지 재생성" if character.reference_image_url else "🎨 이미지 생성"
                            edit_prompt_key = f"edit_prompt_{character.id}"
                            if st.button(button_text, key=f"show_gen_img_for_{character.id}", use_container_width=True):
                                st.session_state[edit_prompt_key] = True
                                st.rerun()
                    
                    # --- 이미지 생성 프롬프트 편집 모드 ---
                    if st.session_state.get(edit_prompt_key, False):
                        st.markdown("#### 🎨 이미지 생성 프롬프트 수정")
                        default_prompt = get_character_image_prompt(character)
                        
                        prompt_text_area_key = f"prompt_text_{character.id}"
                        edited_prompt = st.text_area(
                            "AI에게 전달할 프롬프트입니다. 자유롭게 수정하세요.",
                            value=default_prompt,
                            height=250,
                            key=prompt_text_area_key
                        )
                        
                        p_col1, p_col2, p_col3 = st.columns([2, 1, 1])
                        with p_col1:
                            if st.button("🚀 이미지 생성 실행", key=f"run_gen_img_{character.id}", type="primary", use_container_width=True):
                                with st.spinner(f"🎨 '{character.name}'의 이미지를 생성하고 있습니다... (프롬프트 길이: {len(edited_prompt)})"):
                                    if generate_single_character_image(novel, character, edited_prompt):
                                        st.success(f"'{character.name}'의 이미지가 생성/업데이트되었습니다.")
                                        st.session_state[edit_prompt_key] = False
                                        st.rerun()
                                    # 오류 메시지는 함수 내에서 처리
                        with p_col2:
                            if st.button("🔄 기본값 복원", key=f"reset_prompt_{character.id}", use_container_width=True):
                                st.session_state[prompt_text_area_key] = default_prompt
                                st.rerun()
                        with p_col3:
                            if st.button("❌ 취소", key=f"cancel_gen_img_{character.id}", use_container_width=True):
                                st.session_state[edit_prompt_key] = False
                                st.rerun()
                        st.markdown("---")
                        
                    # --- 등장인물 삭제 버튼 ---
                    delete_char_key = f"confirm_delete_char_{character.id}"
                    if st.session_state.get(delete_char_key, False):
                        del_col1, del_col2 = st.columns([1, 2])
                        with del_col1:
                            if st.button("🗑️ 삭제 확인", key=f"confirm_delete_btn_char_{character.id}", use_container_width=True, type="primary"):
                                delete_character(novel, character)
                                st.success(f"등장인물 '{character.name}'이(가) 삭제되었습니다.")
                                st.session_state[delete_char_key] = False
                                st.rerun()
                        with del_col2:
                            st.warning("정말로 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
                    else:
                        if st.button("🗑️ 등장인물 삭제", key=f"delete_btn_char_{character.id}", use_container_width=True):
                            st.session_state[delete_char_key] = True
                            st.rerun()

                    # 이미지 표시
                    if character.reference_image_url:
                        try:
                            data_manager = st.session_state.data_manager
                            image_data = data_manager.load_image(character.reference_image_url)
                            if image_data:
                                st.image(image_data, caption=f"{character.name} 이미지", width=200)
                            else:
                                st.warning(f"이미지 파일을 찾을 수 없습니다: {character.reference_image_url}")
                                # 이미지 URL 초기화
                                character.reference_image_url = ""
                        except Exception as e:
                            st.error(f"이미지 로딩 오류: {str(e)}")
        else:
            st.info("등장인물이 없습니다.")
            if st.button("🤖 AI로 등장인물 추출하기", use_container_width=True, key="extract_chars_tab2"):
                extract_characters_from_novel(novel)

    with tab3: # 3. 장 관리 탭
        st.subheader("장(Chapter) 관리") 
        
        if novel.chapters:
            # 장 목록 표시
            st.info(f"📚 총 {len(novel.chapters)}개의 장이 있습니다.")
            
            # 장 번호순으로 정렬
            sorted_chapters = sorted(novel.chapters.values(), key=lambda x: x.chapter_number)
            
            for chapter in sorted_chapters:
                with st.expander(f"📖 {chapter.chapter_number}장: {chapter.title}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # 장 내용 표시 (편집 가능)
                        chapter_edit_key = f"edit_chapter_{chapter.id}"
                        edit_chapter = st.checkbox(f"편집 모드", key=chapter_edit_key)
                        
                        if edit_chapter:
                            new_title = st.text_input(
                                "장 제목", 
                                value=chapter.title, 
                                key=f"title_{chapter.id}"
                            )
                            
                            new_content = st.text_area(
                                "장 내용", 
                                value=chapter.content, 
                                height=300,
                                key=f"content_{chapter.id}"
                            )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 저장", key=f"save_{chapter.id}"):
                                    chapter.title = new_title
                                    chapter.content = new_content
                                    
                                    # 저장
                                    data_manager = st.session_state.data_manager
                                    if data_manager.save_novel(novel):
                                        st.session_state.novels[novel.id] = novel
                                        data_manager.save_novels(st.session_state.novels)
                                        st.success("✅ 장이 저장되었습니다!")
                                        st.rerun()
                            
                            with col_cancel:
                                if st.button("❌ 취소", key=f"cancel_{chapter.id}"):
                                    st.rerun()
                        else:
                            # 읽기 전용 표시
                            st.text_area(
                                "장 내용 (읽기 전용)", 
                                value=chapter.content, 
                                height=200, 
                                disabled=True,
                                key=f"readonly_{chapter.id}"
                            )
                    
                    with col2:
                        st.markdown("### 장 정보")
                        st.metric("장 번호", chapter.chapter_number)
                        st.metric("글자 수", f"{len(chapter.content):,}")
                        st.metric("줄 수", f"{len(chapter.content.splitlines()):,}")
                        
                        # 이 장의 장면 수 표시
                        chapter_scenes = [scene for scene in novel.scenes.values() if scene.chapter_id == chapter.id]
                        st.metric("장면 수", f"{len(chapter_scenes)}개")
                        
                        st.markdown("---")
                        
                        # 장면 분리 버튼
                        if st.button("🎬 장면 분리", help="이 장을 장면으로 분리", key=f"split_scenes_{chapter.id}"):
                            with st.spinner(f"{chapter.chapter_number}장을 장면으로 분리하고 있습니다..."):
                                scenes = split_chapter_into_scenes(chapter, novel.characters)
                                if scenes:
                                    # 이 장의 기존 장면 삭제
                                    novel.scenes = {
                                        scene_id: scene for scene_id, scene in novel.scenes.items() 
                                        if scene.chapter_id != chapter.id
                                    }
                                    
                                    # 새 장면 추가
                                    for scene in scenes:
                                        novel.scenes[scene.id] = scene
                                    
                                    # 저장
                                    data_manager = st.session_state.data_manager
                                    if data_manager.save_novel(novel):
                                        st.session_state.novels[novel.id] = novel
                                        data_manager.save_novels(st.session_state.novels)
                                        st.success(f"🎬 {chapter.chapter_number}장에서 {len(scenes)}개 장면 분리 완료!")
                                        st.rerun()
                                    else:
                                        st.error("❌ 장면 분리 저장에 실패했습니다.")
                                else:
                                    st.warning("⚠️ 장면을 분리할 수 없습니다.")
                        
                        # 장면 목록 표시
                        if chapter_scenes:
                            st.markdown("### 장면 목록")
                            for i, scene in enumerate(sorted(chapter_scenes, key=lambda x: x.title), 1):
                                st.text(f"{i}. {scene.title}")
                        
                        st.markdown("---")
                        
                        # 장 삭제 버튼
                        if st.button("🗑️ 장 삭제", key=f"delete_{chapter.id}"):
                            if st.session_state.get(f'confirm_delete_chapter_{chapter.id}', False):
                                # 실제 삭제
                                del novel.chapters[chapter.id]
                                
                                # 저장
                                data_manager = st.session_state.data_manager
                                if data_manager.save_novel(novel):
                                    st.session_state.novels[novel.id] = novel
                                    data_manager.save_novels(st.session_state.novels)
                                    st.success(f"✅ {chapter.chapter_number}장이 삭제되었습니다!")
                                    st.rerun()
                            else:
                                # 삭제 확인 요청
                                st.session_state[f'confirm_delete_chapter_{chapter.id}'] = True
                                st.warning("다시 클릭하면 삭제됩니다.")
                                st.rerun()
        else:
            st.info("장으로 분리된 내용이 없습니다.")
            if novel.script:
                st.markdown("### 장 분리 방법")
                st.markdown("""
                대본에서 다음과 같은 형식으로 장을 구분해주세요:
                - `#1장` 또는 `#1장 제목`
                - `#제1장` 또는 `#제1장 제목`
                - `#2장` 또는 `#2장 제목`
                
                예시:
                ```
                #1장 시작
                첫 번째 장의 내용...
                
                #2장 전개
                두 번째 장의 내용...
                ```
                """)
                
                if st.button("📚 대본을 장으로 분리하기", use_container_width=True):
                    with st.spinner("대본을 장으로 분리하고 있습니다..."):
                        chapters = split_script_into_chapters(novel.script, novel.id)
                        if chapters:
                            # 기존 장 데이터 초기화
                            novel.chapters = {}
                            
                            # 새 장 데이터 추가
                            for chapter in chapters:
                                novel.chapters[chapter.id] = chapter
                            
                            # 저장
                            data_manager = st.session_state.data_manager
                            if data_manager.save_novel(novel):
                                st.session_state.novels[novel.id] = novel
                                data_manager.save_novels(st.session_state.novels)
                                st.success(f"📚 {len(chapters)}개 장으로 분리 완료!")
                                st.rerun()
                            else:
                                st.error("❌ 장 분리 저장에 실패했습니다.")
                        else:
                            st.warning("⚠️ 장 구분자를 찾을 수 없습니다. 위의 형식을 참고해주세요.")
            else:
                st.warning("먼저 대본을 작성해주세요.")
    
    with tab4: # 4. 장면 탭
        st.subheader("장면 관리")
        if novel.scenes:
            # 챕터별로 장면 그룹화
            scenes_by_chapter = {}
            scenes_without_chapter = []
            
            for scene in novel.scenes.values():
                if scene.chapter_id and scene.chapter_id in novel.chapters:
                    chapter = novel.chapters[scene.chapter_id]
                    chapter_key = f"{chapter.chapter_number}장: {chapter.title}"
                    if chapter_key not in scenes_by_chapter:
                        scenes_by_chapter[chapter_key] = []
                    scenes_by_chapter[chapter_key].append(scene)
                else:
                    scenes_without_chapter.append(scene)
            
            # 챕터별 장면 표시
            for chapter_name, scenes in sorted(scenes_by_chapter.items()):
                st.markdown(f"### 📚 {chapter_name}")
                for scene in scenes:
                    with st.expander(f"🎬 {scene.title}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**지문:** {scene.narration}")
                            st.write(f"**대사:** {scene.dialogue}")
                            if scene.casting:
                                character_names = []
                                for char_id in scene.casting:
                                    if char_id in novel.characters:
                                        character_names.append(novel.characters[char_id].name)
                                st.write(f"**등장인물:** {', '.join(character_names)}")
                        with col2:
                            if scene.image_url:
                                try:
                                    # 데이터 관리자를 통해 이미지 로드
                                    data_manager = st.session_state.data_manager
                                    image_data = data_manager.load_image(scene.image_url)
                                    
                                    if image_data:
                                        st.image(image_data, caption=scene.title, width=300)
                                    else:
                                        st.warning(f"이미지 파일을 찾을 수 없습니다: {scene.image_url}")
                                        # 이미지 URL 초기화
                                        scene.image_url = ""
                                except Exception as e:
                                    st.error(f"이미지 로딩 오류: {str(e)}")
                                    # 이미지 URL 초기화
                                    scene.image_url = ""
                        
                        # --- 기능 버튼들 ---
                        st.markdown("---")
                        edit_scene_details_key = f"edit_scene_details_{scene.id}"
                        edit_scene_prompt_key = f"edit_scene_prompt_{scene.id}"

                        # --- 장면 정보 수정 UI ---
                        if st.session_state.get(edit_scene_details_key, False):
                            st.markdown("#### ✏️ 장면 정보 수정")
                            edited_title = st.text_input("제목", value=scene.title, key=f"title_edit_{scene.id}")
                            edited_narration = st.text_area("지문", value=scene.narration, key=f"narration_edit_{scene.id}", height=100)
                            edited_dialogue = st.text_area("대사", value=scene.dialogue, key=f"dialogue_edit_{scene.id}", height=100)
                            
                            character_options = {char_id: char.name for char_id, char in novel.characters.items()}
                            selected_char_ids = st.multiselect(
                                "등장인물 캐스팅",
                                options=character_options.keys(),
                                default=scene.casting,
                                format_func=lambda char_id: character_options.get(char_id, "알 수 없음"),
                                key=f"casting_edit_{scene.id}"
                            )

                            s_col1, s_col2 = st.columns(2)
                            with s_col1:
                                if st.button("💾 정보 저장", key=f"save_details_{scene.id}", use_container_width=True, type="primary"):
                                    scene.title = edited_title
                                    scene.narration = edited_narration
                                    scene.dialogue = edited_dialogue
                                    scene.casting = selected_char_ids
                                    if st.session_state.data_manager.save_novel(novel):
                                        st.success("장면 정보가 저장되었습니다.")
                                        st.session_state[edit_scene_details_key] = False
                                        st.rerun()
                                    else:
                                        st.error("저장에 실패했습니다.")
                            with s_col2:
                                if st.button("❌ 취소", key=f"cancel_details_{scene.id}", use_container_width=True):
                                    st.session_state[edit_scene_details_key] = False
                                    st.rerun()

                        # --- 이미지 프롬프트 수정 UI ---
                        elif st.session_state.get(edit_scene_prompt_key, False):
                            st.markdown("#### 🖼️ 장면 이미지 프롬프트 수정")
                            prompt_dict, _ = get_or_generate_scene_prompt(novel, scene)
                            default_prompt = ", ".join(part for part in prompt_dict.values() if part and isinstance(part, str))

                            prompt_text_area_key = f"prompt_text_scene_{scene.id}"
                            edited_prompt = st.text_area(
                                "AI에게 전달할 프롬프트입니다. 자유롭게 수정하세요.",
                                value=st.session_state.get(prompt_text_area_key, default_prompt),
                                height=250,
                                key=prompt_text_area_key
                            )

                            p_col1, p_col2, p_col3 = st.columns([2, 1, 1])
                            with p_col1:
                                if st.button("🚀 이미지 생성 실행", key=f"run_gen_scene_img_{scene.id}", type="primary", use_container_width=True):
                                    with st.spinner(f"🎨 '{scene.title}' 장면 이미지를 생성하고 있습니다..."):
                                        # 수정된 프롬프트로 이미지 생성, prompt_dict는 로그 및 저장을 위해 전달
                                        if generate_single_scene_image(novel, scene, edited_prompt, prompt_dict):
                                            st.success(f"'{scene.title}' 장면 이미지가 생성/업데이트되었습니다.")
                                            st.session_state[edit_scene_prompt_key] = False
                                            st.rerun()
                            with p_col2:
                                if st.button("🔄 프롬프트 재생성", key=f"reset_scene_prompt_{scene.id}", use_container_width=True):
                                    scene.image_prompt = ""
                                    # 재생성 후 UI에 반영하기 위해 세션의 프롬프트도 초기화
                                    if prompt_text_area_key in st.session_state:
                                        del st.session_state[prompt_text_area_key]
                                    st.rerun()
                            with p_col3:
                                if st.button("❌ 취소", key=f"cancel_gen_scene_img_{scene.id}", use_container_width=True):
                                    st.session_state[edit_scene_prompt_key] = False
                                    st.rerun()
                        else:
                            # --- 기본 버튼 UI ---
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("✏️ 장면 정보 수정", key=f"show_edit_details_{scene.id}", use_container_width=True):
                                    st.session_state[edit_scene_details_key] = True
                                    st.rerun()
                            with btn_col2:
                                img_btn_text = "🎨 이미지 재생성" if scene.image_url else "🎨 이미지 생성"
                                if st.button(img_btn_text, key=f"show_gen_img_{scene.id}", use_container_width=True):
                                    st.session_state[edit_scene_prompt_key] = True
                                    st.rerun()

                        # --- 장면 삭제 버튼 ---
                        st.markdown("---")
                        delete_scene_key = f"confirm_delete_scene_{scene.id}"
                        if st.session_state.get(delete_scene_key, False):
                            del_col1, del_col2 = st.columns([1, 2])
                            with del_col1:
                                if st.button("🗑️ 삭제 확인", key=f"confirm_delete_btn_{scene.id}", use_container_width=True, type="primary"):
                                    delete_scene(novel, scene)
                                    st.success(f"장면 '{scene.title}'이(가) 삭제되었습니다.")
                                    st.session_state[delete_scene_key] = False
                                    st.rerun()
                            with del_col2:
                                st.warning("정말로 삭제하시겠습니까?")
                        else:
                            if st.button("🗑️ 장면 삭제", key=f"delete_btn_{scene.id}", use_container_width=True):
                                st.session_state[delete_scene_key] = True
                                st.rerun()

            # 챕터에 속하지 않는 장면들
            if scenes_without_chapter:
                st.markdown("### 📄 기타 장면")
                for scene in scenes_without_chapter:
                    with st.expander(f"🎬 {scene.title}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**지문:** {scene.narration}")
                            st.write(f"**대사:** {scene.dialogue}")
                            if scene.casting:
                                character_names = [novel.characters[char_id].name for char_id in scene.casting if char_id in novel.characters]
                                st.write(f"**등장인물:** {', '.join(character_names)}")
                        with col2:
                            if scene.image_url:
                                try:
                                    data_manager = st.session_state.data_manager
                                    image_data = data_manager.load_image(scene.image_url)
                                    if image_data:
                                        st.image(image_data, caption=scene.title, width=300)
                                    else:
                                        st.warning(f"이미지 파일을 찾을 수 없습니다: {scene.image_url}")
                                        scene.image_url = ""
                                except Exception as e:
                                    st.error(f"이미지 로딩 오류: {str(e)}")
                                    scene.image_url = ""
                        
                        # --- 기능 버튼들 ---
                        st.markdown("---")
                        edit_scene_details_key = f"edit_scene_details_no_chapter_{scene.id}"
                        edit_scene_prompt_key = f"edit_scene_prompt_no_chapter_{scene.id}"

                        # --- 장면 정보 수정 UI ---
                        if st.session_state.get(edit_scene_details_key, False):
                            st.markdown("#### ✏️ 장면 정보 수정")
                            edited_title = st.text_input("제목", value=scene.title, key=f"title_edit_no_chapter_{scene.id}")
                            edited_narration = st.text_area("지문", value=scene.narration, key=f"narration_edit_no_chapter_{scene.id}", height=100)
                            edited_dialogue = st.text_area("대사", value=scene.dialogue, key=f"dialogue_edit_no_chapter_{scene.id}", height=100)
                            
                            character_options = {char_id: char.name for char_id, char in novel.characters.items()}
                            selected_char_ids = st.multiselect(
                                "등장인물 캐스팅",
                                options=character_options.keys(),
                                default=scene.casting,
                                format_func=lambda char_id: character_options.get(char_id, "알 수 없음"),
                                key=f"casting_edit_no_chapter_{scene.id}"
                            )

                            s_col1, s_col2 = st.columns(2)
                            with s_col1:
                                if st.button("💾 정보 저장", key=f"save_details_no_chapter_{scene.id}", use_container_width=True, type="primary"):
                                    scene.title = edited_title
                                    scene.narration = edited_narration
                                    scene.dialogue = edited_dialogue
                                    scene.casting = selected_char_ids
                                    if st.session_state.data_manager.save_novel(novel):
                                        st.success("장면 정보가 저장되었습니다.")
                                        st.session_state[edit_scene_details_key] = False
                                        st.rerun()
                                    else:
                                        st.error("저장에 실패했습니다.")
                            with s_col2:
                                if st.button("❌ 취소", key=f"cancel_details_no_chapter_{scene.id}", use_container_width=True):
                                    st.session_state[edit_scene_details_key] = False
                                    st.rerun()

                        # --- 이미지 프롬프트 수정 UI ---
                        elif st.session_state.get(edit_scene_prompt_key, False):
                            st.markdown("#### 🖼️ 장면 이미지 프롬프트 수정")
                            prompt_dict, _ = get_or_generate_scene_prompt(novel, scene)
                            default_prompt = ", ".join(part for part in prompt_dict.values() if part and isinstance(part, str))

                            prompt_text_area_key = f"prompt_text_scene_no_chapter_{scene.id}"
                            edited_prompt = st.text_area(
                                "AI에게 전달할 프롬프트입니다. 자유롭게 수정하세요.",
                                value=st.session_state.get(prompt_text_area_key, default_prompt),
                                height=250,
                                key=prompt_text_area_key
                            )

                            p_col1, p_col2, p_col3 = st.columns([2, 1, 1])
                            with p_col1:
                                if st.button("🚀 이미지 생성 실행", key=f"run_gen_scene_img_no_chapter_{scene.id}", type="primary", use_container_width=True):
                                    with st.spinner(f"🎨 '{scene.title}' 장면 이미지를 생성하고 있습니다..."):
                                        if generate_single_scene_image(novel, scene, edited_prompt, prompt_dict):
                                            st.success(f"'{scene.title}' 장면 이미지가 생성/업데이트되었습니다.")
                                            st.session_state[edit_scene_prompt_key] = False
                                            st.rerun()
                            with p_col2:
                                if st.button("🔄 프롬프트 재생성", key=f"reset_scene_prompt_no_chapter_{scene.id}", use_container_width=True):
                                    scene.image_prompt = ""
                                    if prompt_text_area_key in st.session_state:
                                        del st.session_state[prompt_text_area_key]
                                    st.rerun()
                            with p_col3:
                                if st.button("❌ 취소", key=f"cancel_gen_scene_img_no_chapter_{scene.id}", use_container_width=True):
                                    st.session_state[edit_scene_prompt_key] = False
                                    st.rerun()
                        else:
                            # --- 기본 버튼 UI ---
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("✏️ 장면 정보 수정", key=f"show_edit_details_no_chapter_{scene.id}", use_container_width=True):
                                    st.session_state[edit_scene_details_key] = True
                                    st.rerun()
                            with btn_col2:
                                img_btn_text = "🎨 이미지 재생성" if scene.image_url else "🎨 이미지 생성"
                                if st.button(img_btn_text, key=f"show_gen_img_no_chapter_{scene.id}", use_container_width=True):
                                    st.session_state[edit_scene_prompt_key] = True
                                    st.rerun()

                        # --- 장면 삭제 버튼 ---
                        st.markdown("---")
                        delete_scene_key = f"confirm_delete_scene_no_chapter_{scene.id}"
                        if st.session_state.get(delete_scene_key, False):
                            del_col1, del_col2 = st.columns([1, 2])
                            with del_col1:
                                if st.button("🗑️ 삭제 확인", key=f"confirm_delete_btn_no_chapter_{scene.id}", use_container_width=True, type="primary"):
                                    delete_scene(novel, scene)
                                    st.success(f"장면 '{scene.title}'이(가) 삭제되었습니다.")
                                    st.session_state[delete_scene_key] = False
                                    st.rerun()
                            with del_col2:
                                st.warning("정말로 삭제하시겠습니까?")
                        else:
                            if st.button("🗑️ 장면 삭제", key=f"delete_btn_no_chapter_{scene.id}", use_container_width=True):
                                st.session_state[delete_scene_key] = True
                                st.rerun()
        else:
            st.info("장면이 없습니다.")
            
            # 전체 대본 장면 분리 (기존 방식)
            if novel.script and not novel.chapters:
                if st.button("🤖 전체 대본 장면 분리", use_container_width=True, key="split_scenes_tab4"):
                    split_scenes_from_novel(novel)
            
            # 챕터별 장면 분리 안내
            if novel.chapters:
                st.markdown("### 💡 챕터별 장면 분리")
                st.info("각 장을 개별적으로 장면으로 분리하려면 '📚 장 관리' 탭에서 해당 장의 '🎬 장면 분리' 버튼을 사용하세요.")
            else:
                st.markdown("### 💡 장면 분리 방법")
                st.info("먼저 '📚 장 관리' 탭에서 대본을 장으로 분리한 후, 각 장을 개별적으로 장면으로 분리하는 것을 권장합니다.")
    
    with tab5: # 5. AI 분석 탭
        st.subheader("AI 분석 및 생성")
        
        # API 키 확인
        from src.security import get_secure_api_key
        api_key = get_secure_api_key('gemini')
        
        if not api_key:
            st.error("🔑 제미나이 API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
            return
        
        st.success("🔑 API 키가 설정되어 있습니다. AI 기능을 사용할 수 있습니다!")
        
        # API 연결 테스트
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🔍 API 연결 테스트", help="제미나이 API 연결 상태를 확인합니다"):
                with st.spinner("API 연결을 테스트하고 있습니다..."):
                    from src.api_clients import GeminiClient
                    client = GeminiClient()
                    
                    if client.test_api_connection():
                        st.success("✅ API 연결이 정상입니다!")
                    else:
                        st.error("❌ API 연결에 실패했습니다.")
                        
                        with st.expander("🔧 문제 해결 방법"):
                            st.markdown("""
                            **API 연결 실패 시 확인사항:**
                            1. **API 키 확인**: .streamlit/secrets.toml 파일의 GEMINI_API_KEY 값
                            2. **인터넷 연결**: 네트워크 연결 상태 확인
                            3. **방화벽 설정**: generativelanguage.googleapis.com 접근 허용
                            4. **API 할당량**: Google AI Studio에서 할당량 확인
                            5. **API 키 권한**: API 키가 활성화되어 있는지 확인
                            """)
        
        with col2:
            st.info("연결 테스트로 문제를 미리 확인하세요")
        
        st.markdown("---")
        
        # 1단계: 등장인물 추출
        st.markdown("### 1단계: 등장인물 추출")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🤖 등장인물 자동 추출", use_container_width=True, key="extract_characters"):
                extract_characters_from_novel(novel)
        
        with col2:
            if novel.characters:
                st.success(f"✅ {len(novel.characters)}명 추출됨")
            else:
                st.info("대기 중")
        
        # 2단계: 등장인물 이미지 생성
        st.markdown("### 2단계: 등장인물 이미지 생성")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if novel.characters:
                if st.button("🎨 등장인물 이미지 생성", use_container_width=True, key="generate_character_images"):
                    generate_character_images(novel)
            else:
                st.button("🎨 등장인물 이미지 생성", disabled=True, use_container_width=True, help="먼저 등장인물을 추출해주세요")
        
        with col2:
            if novel.characters:
                images_count = sum(1 for char in novel.characters.values() if char.reference_image_url)
                if images_count > 0:
                    st.success(f"✅ {images_count}개 생성됨")
                else:
                    st.info("대기 중")
            else:
                st.info("대기 중")
        
        # 3단계: 장면 분리
        st.markdown("### 3단계: 장면 분리")
        
        if novel.chapters:
            # 챕터별 장면 분리
            st.info("💡 장으로 분리된 대본입니다. 각 장을 개별적으로 장면 분리하는 것을 권장합니다.")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("🎬 모든 장 장면 분리", use_container_width=True, key="split_all_chapters"):
                    split_all_chapters_into_scenes(novel)
            
            with col2:
                if novel.scenes:
                    st.success(f"✅ {len(novel.scenes)}개 분리됨")
                else:
                    st.info("대기 중")
            
            # 개별 장 분리 옵션
            st.markdown("#### 개별 장 분리")
            chapters_without_scenes = []
            for chapter in sorted(novel.chapters.values(), key=lambda x: x.chapter_number):
                chapter_scenes = [s for s in novel.scenes.values() if s.chapter_id == chapter.id]
                if not chapter_scenes:
                    chapters_without_scenes.append(chapter)
            
            if chapters_without_scenes:
                selected_chapter = st.selectbox(
                    "장면 분리할 장 선택:",
                    options=chapters_without_scenes,
                    format_func=lambda x: f"{x.chapter_number}장: {x.title}",
                    key="select_chapter_for_scenes"
                )
                
                if st.button(f"🎬 {selected_chapter.chapter_number}장만 장면 분리", key="split_selected_chapter"):
                    with st.spinner(f"{selected_chapter.chapter_number}장을 장면으로 분리하고 있습니다..."):
                        scenes = split_chapter_into_scenes(selected_chapter, novel.characters)
                        if scenes:
                            # 새 장면 추가
                            for scene in scenes:
                                novel.scenes[scene.id] = scene
                            
                            # 저장
                            data_manager = st.session_state.data_manager
                            if data_manager.save_novel(novel):
                                st.session_state.novels[novel.id] = novel
                                data_manager.save_novels(st.session_state.novels)
                                st.success(f"🎬 {selected_chapter.chapter_number}장에서 {len(scenes)}개 장면 분리 완료!")
                                st.rerun()
        else:
            # 전체 대본 장면 분리 (기존 방식)
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if st.button("🎬 전체 대본 장면 분리", use_container_width=True, key="split_scenes"):
                    split_scenes_from_novel(novel)
            
            with col2:
                if novel.scenes:
                    st.success(f"✅ {len(novel.scenes)}개 분리됨")
                else:
                    st.info("대기 중")
            
            st.info("💡 대용량 대본의 경우 먼저 장으로 분리한 후 챕터별로 장면 분리하는 것을 권장합니다.")
        
        # 4단계: 장면 이미지 생성
        st.markdown("### 4단계: 장면 이미지 생성")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if novel.scenes and novel.characters:
                if st.button("🖼️ 장면 이미지 생성", use_container_width=True, key="generate_scene_images"):
                    generate_scene_images(novel)
            else:
                st.button("🖼️ 장면 이미지 생성", disabled=True, use_container_width=True, help="먼저 등장인물과 장면을 생성해주세요")
        
        with col2:
            if novel.scenes:
                images_count = sum(1 for scene in novel.scenes.values() if scene.image_url)
                if images_count > 0:
                    st.success(f"✅ {images_count}개 생성됨")
                else:
                    st.info("대기 중")
            else:
                st.info("대기 중")
        
        # 전체 자동화 버튼
        st.markdown("---")
        st.markdown("### 🚀 전체 자동화")
        if st.button("🤖 모든 단계 자동 실행", use_container_width=True, type="primary", key="auto_all"):
            run_full_automation(novel)


def extract_characters_from_novel(novel: Novel):
    """소설에서 등장인물 추출"""
    try:
        from src.api_clients import GeminiClient
        
        with st.spinner("🤖 AI가 등장인물을 추출하고 있습니다..."):
            gemini_client = GeminiClient()
            character_data = gemini_client.extract_characters_from_script(novel.script)
            
            if character_data:
                # 등장인물 객체 생성
                for char_info in character_data:                    
                    character = Character(
                        id=generate_uuid(),
                        novel_id=novel.id,
                        name=char_info['name'],
                        description=char_info['description'],
                        reference_image_url="",
                        created_at=datetime.now()
                    )
                    novel.characters[character.id] = character
                
                # 데이터 저장
                data_manager = st.session_state.data_manager
                data_manager.save_novel(novel)
                st.session_state.novels[novel.id] = novel
                data_manager.save_novels(st.session_state.novels)
                
                st.success(f"✅ {len(character_data)}명의 등장인물이 추출되었습니다!")
                st.rerun()
            else:
                st.error("❌ 등장인물을 추출할 수 없습니다.")
                
    except Exception as e:
        st.error(f"❌ 등장인물 추출 실패: {str(e)}")


def generate_character_images(novel: Novel):
    """등장인물 이미지 생성"""
    try:
        from src.api_clients import GeminiImageClient
        
        characters_without_images = [char for char in novel.characters.values() if not char.reference_image_url]
        
        if not characters_without_images:
            st.info("모든 등장인물의 이미지가 이미 생성되었습니다.")
            return
        
        total_chars = len(characters_without_images)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        image_client = GeminiImageClient()
        data_manager = st.session_state.data_manager
        
        for i, character in enumerate(characters_without_images):
            status_text.text(f"🎨 {character.name}의 이미지 생성 중... ({i+1}/{total_chars})")
            progress_bar.progress((i + 1) / total_chars)
            
            # 이미지 생성
            image_data = image_client.generate_character_reference_image(character.description)
            
            if image_data:
                # 이미지 압축
                from src.image_utils import optimize_for_web
                compressed_image = optimize_for_web(image_data)
                
                if compressed_image:
                    # 이미지 저장
                    image_path = data_manager.save_character_image(novel.id, character.id, compressed_image)
                    character.reference_image_url = image_path
                    
                    # 소설 업데이트
                    novel.characters[character.id] = character
            
            # API 호출 간격 조절
            import time
            time.sleep(1)
        
        # 데이터 저장
        data_manager.save_novel(novel)
        st.session_state.novels[novel.id] = novel
        data_manager.save_novels(st.session_state.novels)
        
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✅ {total_chars}명의 등장인물 이미지가 생성되었습니다!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 등장인물 이미지 생성 실패: {str(e)}")


def get_character_image_prompt(character: Character) -> str:
    """등장인물 이미지 생성을 위한 기본 프롬프트를 생성합니다."""
    return f"""
유튜브 소설에 사용할 등장인물의 레퍼런스 이미지를 생성해줘. 이 프롬프트에 대한 응답으로 이미지를 생성해야 해.
- 인물: 한국인
- 배경: 단색의 깔끔한 배경 (흰색 또는 회색)
- 구도: 상반신이 잘 보이는 정면 또는 약간 측면의 인물 사진 (Bust shot), 사진은 1컷만 생성
- 스타일: 스튜디오 조명, 하이퍼리얼리즘, 4k, 고화질
- 인물 상세 묘사: {character.description}
""".strip()


def generate_single_character_image(novel: Novel, character: Character, prompt: str) -> bool:
    """특정 등장인물 한 명의 이미지를 생성"""
    try:
        from src.api_clients import GeminiImageClient
        from src.image_utils import optimize_for_web

        if not prompt.strip():
            st.error("❌ 프롬프트 내용이 비어있습니다.")
            return False

        image_client = GeminiImageClient()
        data_manager = st.session_state.data_manager

        # 이미지 생성
        image_data = image_client.generate_character_reference_image(prompt)

        if image_data:
            # 이미지 압축
            compressed_image = optimize_for_web(image_data)

            if compressed_image:
                # 이미지 저장
                image_path = data_manager.save_character_image(novel.id, character.id, compressed_image)
                character.reference_image_url = image_path

                # 소설 데이터 업데이트 및 저장
                novel.characters[character.id] = character
                if data_manager.save_novel(novel):
                    st.session_state.novels[novel.id] = novel
                    data_manager.save_novels(st.session_state.novels)
                    return True
                else:
                    st.error("이미지 정보 저장에 실패했습니다.")
                    return False
            else:
                st.error("이미지 압축에 실패했습니다.")
                return False
        else:
            st.error("이미지 생성에 실패했습니다. API 응답이 없습니다.")
            return False

    except Exception as e:
        st.error(f"❌ '{character.name}' 이미지 생성 실패: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return False

def generate_single_scene_image(novel: Novel, scene: Scene, prompt: str, prompt_dict: dict) -> bool:
    """특정 장면 하나의 이미지를 생성"""
    print(f"\n[이미지 생성 시작] 장면: '{scene.title}' (ID: {scene.id})")
    try:
        from src.api_clients import GeminiImageClient
        from src.image_utils import optimize_for_web

        if not prompt.strip():
            print("[이미지 생성 실패] 프롬프트 내용이 비어있습니다.")
            st.error("❌ 프롬프트 내용이 비어있습니다.")
            return False

        image_client = GeminiImageClient()
        data_manager = st.session_state.data_manager

        print("[이미지 생성 정보] 등장인물 기준 이미지 수집 중...")
        reference_images = []
        scene_characters = [novel.characters[char_id] for char_id in scene.casting if char_id in novel.characters]
        for character in scene_characters:
            if character.reference_image_url:
                image_data = data_manager.load_image(character.reference_image_url)
                if image_data:
                    reference_images.append(image_data)

        print(f"[이미지 생성 정보] 최종 프롬프트 길이: {len(prompt)} 문자")
        print(f"[이미지 생성 정보] 기준 이미지 개수: {len(reference_images)}개")

        # 4. 장면 이미지 생성
        scene.image_prompt = prompt_dict # 사용된 프롬프트를 딕셔너리 형태로 저장
        scene_image_data = image_client.generate_scene_image(prompt, reference_images)

        if scene_image_data:
            # 이미지 압축
            compressed_image = optimize_for_web(scene_image_data)
            if not compressed_image:
                print("[이미지 생성 실패] 이미지 압축에 실패했습니다.")
                st.error("이미지 압축에 실패했습니다.")
                return False

            # 이미지 저장
            scene_image_path = data_manager.save_scene_image(novel.id, scene.id, compressed_image)
            scene.image_url = scene_image_path

            # 소설 데이터 업데이트 및 저장
            novel.scenes[scene.id] = scene
            if data_manager.save_novel(novel):
                st.session_state.novels[novel.id] = novel
                data_manager.save_novels(st.session_state.novels)
                print(f"[이미지 생성 성공] 장면 '{scene.title}'의 이미지가 성공적으로 저장되었습니다.")
                return True
        else:
            # API 호출이 실패하여 scene_image_data가 None일 경우
            print(f"[이미지 생성 실패] API 클라이언트가 이미지 데이터를 반환하지 않았습니다 (scene_image_data is None).")
            st.error("❌ 이미지 생성 API 호출에 실패했습니다. API 클라이언트 로그를 확인해주세요.")
            return False
            
    except Exception as e:
        import traceback
        print(f"[이미지 생성 예외] 장면 '{scene.title}' 처리 중 오류 발생: {str(e)}")
        print(traceback.format_exc())
        st.error(f"❌ '{scene.title}' 장면 이미지 생성 실패: {str(e)}")
        return False

def delete_character(novel: Novel, character: Character):
    """소설에서 특정 등장인물을 삭제합니다."""
    try:
        data_manager = st.session_state.data_manager

        # 1. novel.characters 딕셔너리에서 등장인물 제거
        if character.id in novel.characters:
            # 2. 이미지 파일 삭제
            if character.reference_image_url:
                image_path = Path(data_manager.data_dir) / character.reference_image_url
                if image_path.exists():
                    image_path.unlink()

            del novel.characters[character.id]

            # 3. 이 등장인물을 캐스팅한 모든 장면에서 제거
            for scene in novel.scenes.values():
                if character.id in scene.casting:
                    scene.casting.remove(character.id)

            # 4. 변경사항 저장
            if data_manager.save_novel(novel):
                st.session_state.novels[novel.id] = novel
                data_manager.save_novels(st.session_state.novels)
    except Exception as e:
        st.error(f"등장인물 삭제 중 오류 발생: {str(e)}")

def delete_scene(novel: Novel, scene: Scene):
    """소설에서 특정 장면을 삭제합니다."""
    try:
        # 1. novel.scenes 딕셔너리에서 장면 제거
        if scene.id in novel.scenes:
            del novel.scenes[scene.id]

        # 2. 데이터 관리자를 통해 변경사항 저장
        data_manager = st.session_state.data_manager
        if data_manager.save_novel(novel):
            # 3. 세션 상태의 novels 목록도 업데이트
            st.session_state.novels[novel.id] = novel
            data_manager.save_novels(st.session_state.novels)
        else:
            st.error("장면 삭제 후 파일 저장에 실패했습니다.")
    except Exception as e:
        st.error(f"장면 삭제 중 오류 발생: {str(e)}")

def get_or_generate_scene_prompt(novel: Novel, scene: Scene) -> tuple[dict, bool]:
    """장면의 이미지 프롬프트가 없으면 생성하고, 있으면 반환합니다."""
    if scene.image_prompt and isinstance(scene.image_prompt, dict):
        return scene.image_prompt, False # 이미 dict 형태로 저장되어 있다고 가정

    try:
        from src.api_clients import GeminiClient
        gemini_client = GeminiClient()
        
        with st.spinner("📝 AI가 이미지 프롬프트를 생성하고 있습니다..."):
            scene_characters = [novel.characters[char_id] for char_id in scene.casting if char_id in novel.characters]
            prompt = gemini_client.generate_scene_prompt(scene, scene_characters)
            if prompt:
                scene.image_prompt = prompt
                return prompt, True
            else:
                # 생성 실패 시, 기존 프롬프트가 있다면 유지, 없다면 빈 딕셔너리 반환
                return scene.image_prompt if isinstance(scene.image_prompt, dict) else {}, False
    except Exception as e:
        # 오류 발생 시, 기존 프롬프트가 있다면 유지, 없다면 오류 메시지 포함 딕셔너리 반환
        return scene.image_prompt if isinstance(scene.image_prompt, dict) else {"error": f"프롬프트 생성 중 오류 발생: {e}"}, False

def split_scenes_from_novel(novel: Novel):
    """소설에서 장면 분리"""
    try:
        from src.api_clients import GeminiClient
        
        print(f"[메인] 장면 분리 시작 - 소설: '{novel.title}'")
        print(f"[메인] 대본 길이: {len(novel.script)} 문자")
        
        # 대본 길이에 따른 예상 시간 안내
        estimated_time = "30초-1분"
        if len(novel.script) > 8000:
            estimated_time = "1-2분"
        if len(novel.script) > 15000:
            estimated_time = "2-3분"
        
        with st.spinner(f"🎬 AI가 장면을 분리하고 있습니다... (예상 시간: {estimated_time})"):
            print("[메인] GeminiClient 초기화 중...")
            gemini_client = GeminiClient()
            print("[메인] 장면 분리 API 호출 중...")
            
            # 진행 상황 표시
            progress_placeholder = st.empty()
            progress_placeholder.info("📡 제미나이 API에 요청을 전송하고 있습니다...")
            
            scene_data = gemini_client.split_script_into_scenes(novel.script)
            
            progress_placeholder.empty()
            
            if scene_data:
                print(f"[메인] 장면 데이터 수신 완료 - {len(scene_data)}개 장면")
                print("[메인] 장면 객체 생성 중...")
                
                # 장면 객체 생성
                for i, scene_info in enumerate(scene_data):
                    print(f"[메인] 장면 {i+1}/{len(scene_data)} 처리 중: {scene_info.get('title', '제목 없음')}")
                    
                    scene = Scene(
                        id=generate_uuid(),
                        novel_id=novel.id,
                        title=scene_info.get('title', '제목 없는 장면'),
                        storyboard=scene_info.get('storyboard', ''),
                        narration=scene_info.get('narration', ''),
                        dialogue=scene_info.get('dialogue', ''),
                        casting=[],  # 나중에 매칭
                        mise_en_scene=scene_info.get('mise_en_scene', ''),
                        image_prompt="",
                        image_url="",
                        created_at=datetime.now()
                    )
                    
                    # 등장인물 매칭
                    print(f"[메인] 장면 '{scene.title}'에 등장인물 매칭 중...")
                    scene_characters = match_characters_to_scene(scene_info, novel.characters)
                    scene.casting = [char.id for char in scene_characters]
                    print(f"[메인] 매칭된 등장인물: {[char.name for char in scene_characters]}")
                    
                    novel.scenes[scene.id] = scene
                
                print("[메인] 모든 장면 처리 완료, 데이터 저장 중...")
                
                # 데이터 저장
                data_manager = st.session_state.data_manager
                data_manager.save_novel(novel)
                st.session_state.novels[novel.id] = novel
                data_manager.save_novels(st.session_state.novels)
                
                print(f"[메인] 장면 분리 완료! 총 {len(scene_data)}개 장면 생성됨")
                st.success(f"✅ {len(scene_data)}개의 장면이 분리되었습니다!")
                st.rerun()
            else:
                print("[메인] 장면 분리 실패 - 장면 데이터 없음")
                st.error("❌ 장면을 분리할 수 없습니다.")
                
    except Exception as e:
        print(f"[메인] 장면 분리 예외 발생: {str(e)}")
        st.error(f"❌ 장면 분리 실패: {str(e)}")


def generate_scene_images(novel: Novel):
    """장면 이미지 생성"""
    try:
        from src.api_clients import GeminiClient, GeminiImageClient
        
        scenes_without_images = [scene for scene in novel.scenes.values() if not scene.image_url]
        
        if not scenes_without_images:
            st.info("모든 장면의 이미지가 이미 생성되었습니다.")
            return
        
        total_scenes = len(scenes_without_images)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        gemini_client = GeminiClient()
        image_client = GeminiImageClient()
        data_manager = st.session_state.data_manager
        
        for i, scene in enumerate(scenes_without_images):
            status_text.text(f"🖼️ '{scene.title}' 이미지 생성 중... ({i+1}/{total_scenes})")
            progress_bar.progress((i + 1) / total_scenes)
            
            # 장면의 등장인물들 찾기
            scene_characters = [novel.characters[char_id] for char_id in scene.casting if char_id in novel.characters]
            
            # 이미지 프롬프트 생성
            scene.image_prompt = gemini_client.generate_scene_prompt(scene, scene_characters)
            
            # 등장인물 기준 이미지들 수집
            reference_images = []
            for character in scene_characters:
                if character.reference_image_url:
                    image_data = data_manager.load_image(character.reference_image_url)
                    if image_data:
                        reference_images.append(image_data)
            
            # 장면 이미지 생성
            scene_image_data = image_client.generate_scene_image(scene.image_prompt, reference_images)
            
            if scene_image_data:
                # 이미지 압축
                from src.image_utils import optimize_for_web
                compressed_image = optimize_for_web(scene_image_data)
                
                if compressed_image:
                    # 이미지 저장
                    scene_image_path = data_manager.save_scene_image(novel.id, scene.id, compressed_image)
                    scene.image_url = scene_image_path
                    
                    # 소설 업데이트
                    novel.scenes[scene.id] = scene
            
            # API 호출 간격 조절
            import time
            time.sleep(1)
        
        # 데이터 저장
        data_manager.save_novel(novel)
        st.session_state.novels[novel.id] = novel
        data_manager.save_novels(st.session_state.novels)
        
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✅ {total_scenes}개의 장면 이미지가 생성되었습니다!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 장면 이미지 생성 실패: {str(e)}")


def preprocess_script_whitespace(script: str) -> str:
    """대본의 공백과 줄바꿈 정리"""
    try:
        if not script:
            return script
        
        import re
        
        # 1. 연속된 공백을 하나로
        script = re.sub(r' +', ' ', script)
        
        # 2. 연속된 줄바꿈을 최대 2개로 제한
        script = re.sub(r'\n{3,}', '\n\n', script)
        
        # 3. 각 줄의 앞뒤 공백 제거 (빈 줄은 유지)
        lines = []
        for line in script.split('\n'):
            if line.strip():
                lines.append(line.strip())
            else:
                lines.append('')
        
        # 4. 전체 앞뒤 공백 제거
        result = '\n'.join(lines).strip()
        
        return result
        
    except Exception as e:
        st.error(f"공백 정리 중 오류: {str(e)}")
        return script

def preprocess_script_remove_duplicate_newlines(script: str) -> str:
    """대본의 연속된 줄바꿈을 하나로 합칩니다."""
    try:
        if not script:
            return script

        import re

        # 1. 모든 연속된 줄바꿈(2개 이상)을 단일 줄바꿈으로 변경
        # 이렇게 하면 문단 구분이 사라지고 모든 줄이 붙게 될 수 있습니다.
        # 따라서 먼저 각 줄의 앞뒤 공백을 제거하고, 빈 줄을 완전히 없앤 후,
        # 모든 내용을 합쳤다가 다시 줄바꿈으로 나누는 것이 더 안전합니다.
        lines = script.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        result = '\n'.join(non_empty_lines)

        return result

    except Exception as e:
        st.error(f"중복 줄바꿈 제거 중 오류: {str(e)}")
        return script

def preprocess_script_paragraphs(script: str) -> str:
    """대본의 문단 구분 정리"""
    try:
        if not script:
            return script
            
        import re
        
        # 장면 구분자 패턴 (제1장, 1장, 장면1 등)
        scene_patterns = [
            r'제\s*\d+\s*장',
            r'\d+\s*장',
            r'장면\s*\d+',
            r'Scene\s*\d+',
            r'SCENE\s*\d+'
        ]
        
        lines = script.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            if not line:
                # 빈 줄은 그대로 유지 (연속된 빈 줄은 하나로)
                if not processed_lines or processed_lines[-1]:
                    processed_lines.append('')
                continue
                
            # 장면 구분자인지 확인
            is_scene_marker = any(re.search(pattern, line, re.IGNORECASE) for pattern in scene_patterns)
            
            if is_scene_marker:
                # 장면 구분자 앞에 빈 줄 추가
                if processed_lines and processed_lines[-1]:
                    processed_lines.append('')
                processed_lines.append(line)
                processed_lines.append('')  # 장면 구분자 뒤에도 빈 줄
            else:
                processed_lines.append(line)
        
        result = '\n'.join(processed_lines)
        print(f"[전처리] 문단 정리 완료 - 원본: {len(lines)} 줄 → 결과: {len(processed_lines)} 줄")
        return result
    except Exception as e:
        print(f"[전처리] 문단 정리 오류: {str(e)}")
        st.error(f"문단 정리 중 오류: {str(e)}")
        return script


def preprocess_script_special_chars(script: str) -> str:
    """대본의 불필요한 특수문자 제거 (. , ! ? ' ` 제외)"""
    try:
        if not script:
            return script
        
        # 유지할 특수문자 정의
        keep_chars = set('.!?\'`,()[]{}""''""：:;-')
        
        # 문자 필터링
        cleaned_chars = []
        for char in script:
            # 한글, 영문, 숫자, 공백, 유지할 특수문자만 남기기
            if (char.isalnum() or 
                char.isspace() or 
                char in keep_chars or
                '\uAC00' <= char <= '\uD7A3' or  # 한글 완성형
                '\u3131' <= char <= '\u318E'):   # 한글 자모
                cleaned_chars.append(char)
        
        result = ''.join(cleaned_chars)
        
        # 후처리: 연속된 공백 정리
        import re
        result = re.sub(r' +', ' ', result)
        result = re.sub(r'\n +', '\n', result)
        result = re.sub(r' +\n', '\n', result)
        
        return result
        
    except Exception as e:
        st.error(f"특수문자 정리 중 오류: {str(e)}")
        return script


def split_all_chapters_into_scenes(novel):
    """모든 장을 장면으로 분리"""
    try:
        if not novel.chapters:
            st.warning("⚠️ 분리할 장이 없습니다.")
            return
        
        total_chapters = len(novel.chapters)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_scenes = []
        
        for i, chapter in enumerate(sorted(novel.chapters.values(), key=lambda x: x.chapter_number)):
            status_text.text(f"🎬 {chapter.chapter_number}장 장면 분리 중... ({i+1}/{total_chapters})")
            progress_bar.progress((i + 1) / total_chapters)
            
            # 이미 장면이 있는 장은 건너뛰기
            existing_scenes = [s for s in novel.scenes.values() if s.chapter_id == chapter.id]
            if existing_scenes:
                status_text.text(f"⏭️ {chapter.chapter_number}장은 이미 장면이 있어서 건너뜀")
                continue
            
            scenes = split_chapter_into_scenes(chapter, novel.characters)
            all_scenes.extend(scenes)
            
            # API 호출 간격 조절
            import time
            time.sleep(1)
        
        if all_scenes:
            # 새 장면들 추가
            for scene in all_scenes:
                novel.scenes[scene.id] = scene
            
            # 저장
            data_manager = st.session_state.data_manager
            if data_manager.save_novel(novel):
                st.session_state.novels[novel.id] = novel
                data_manager.save_novels(st.session_state.novels)
                
                progress_bar.empty()
                status_text.empty()
                
                st.success(f"🎬 모든 장에서 총 {len(all_scenes)}개 장면 분리 완료!")
                st.rerun()
            else:
                st.error("❌ 장면 분리 저장에 실패했습니다.")
        else:
            progress_bar.empty()
            status_text.empty()
            st.info("분리할 새로운 장면이 없습니다.")
            
    except Exception as e:
        st.error(f"전체 장면 분리 실패: {str(e)}")


def split_chapter_into_scenes(chapter, characters: dict) -> list:
    """특정 장을 장면으로 분리"""
    try:
        from src.api_clients import GeminiClient
        from src.models import generate_uuid
        
        if not chapter.content:
            return []
        
        print(f"[장면 분리] {chapter.chapter_number}장 장면 분리 시작 - 내용 길이: {len(chapter.content)} 문자")
        
        gemini_client = GeminiClient()
        scene_data = gemini_client.split_script_into_scenes(chapter.content)
        
        if not scene_data:
            print(f"[장면 분리] {chapter.chapter_number}장 장면 분리 실패 - 장면 데이터 없음")
            return []
        
        scenes = []
        for i, scene_info in enumerate(scene_data):
            scene = Scene(
                id=generate_uuid(),
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,  # 소속 장 ID 설정
                title=scene_info.get('title', f'{chapter.chapter_number}장 장면 {i+1}'),
                storyboard=scene_info.get('storyboard', ''),
                narration=scene_info.get('narration', ''),
                dialogue=scene_info.get('dialogue', ''),
                casting=[],  # 나중에 매칭
                mise_en_scene=scene_info.get('mise_en_scene', ''),
                image_prompt="",
                image_url="",
                created_at=datetime.now()
            )
            
            # 등장인물 매칭
            scene_characters = match_characters_to_scene(scene_info, characters)
            scene.casting = [char.id for char in scene_characters]
            
            scenes.append(scene)
        
        print(f"[장면 분리] {chapter.chapter_number}장 장면 분리 완료 - {len(scenes)}개 장면 생성")
        return scenes
        
    except Exception as e:
        print(f"[장면 분리] {chapter.chapter_number}장 장면 분리 오류: {str(e)}")
        st.error(f"장면 분리 중 오류: {str(e)}")
        return []


def split_script_into_chapters(script: str, novel_id: str) -> list:
    """대본을 장으로 분리"""
    try:
        if not script:
            return []
        
        import re
        from src.models import Chapter, generate_uuid
        
        # 장 구분자 패턴 (#1장, #2장, #제1장, #제2장 등)
        chapter_pattern = r'^#\s*(?:제\s*)?(\d+)\s*장\s*(.*)$'
        
        lines = script.split('\n')
        chapters = []
        current_chapter = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # 장 구분자 확인
            match = re.match(chapter_pattern, line, re.IGNORECASE)
            
            if match:
                # 이전 장 저장
                if current_chapter is not None:
                    current_chapter.content = '\n'.join(current_content).strip()
                    chapters.append(current_chapter)
                
                # 새 장 시작
                chapter_number = int(match.group(1))
                chapter_title = match.group(2).strip() or f"{chapter_number}장"
                
                current_chapter = Chapter(
                    id=generate_uuid(),
                    novel_id=novel_id,
                    chapter_number=chapter_number,
                    title=chapter_title,
                    content=""
                )
                current_content = []
            else:
                # 현재 장의 내용에 추가
                if current_chapter is not None:
                    current_content.append(line)
        
        # 마지막 장 저장
        if current_chapter is not None:
            current_chapter.content = '\n'.join(current_content).strip()
            chapters.append(current_chapter)
        
        # 장 번호순으로 정렬
        chapters.sort(key=lambda x: x.chapter_number)
        
        return chapters
        
    except Exception as e:
        st.error(f"장 분리 중 오류: {str(e)}")
        return []


def preprocess_script_dialogue(script: str) -> str:
    """대본의 대사 형식 표준화"""
    try:
        if not script:
            return script
            
        import re
        
        lines = script.split('\n')
        processed_lines = []
        dialogue_count = 0
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            if not line:
                processed_lines.append('')
                continue
            
            # 대사 패턴 감지 및 표준화
            # 패턴: "이름:" 또는 "이름 :" 또는 "이름말:" 또는 "이름："
            dialogue_pattern = r'^([가-힣a-zA-Z0-9\s]+)\s*[:：]\s*(.+)$'
            match = re.match(dialogue_pattern, line)
            
            if match:
                speaker = match.group(1).strip()
                dialogue = match.group(2).strip()
                
                # 화자 이름이 너무 길면 대사가 아닐 가능성이 높음
                if len(speaker) <= 10 and dialogue:
                    # 표준 형식으로 변환: "이름: 대사"
                    processed_lines.append(f"{speaker}: {dialogue}")
                    dialogue_count += 1
                else:
                    # 대사가 아닌 경우 그대로 유지
                    processed_lines.append(line)
            else:
                # 대사가 아닌 경우 그대로 유지
                processed_lines.append(line)
        
        result = '\n'.join(processed_lines)
        print(f"[전처리] 대사 정리 완료 - {dialogue_count}개 대사 표준화")
        return result
    except Exception as e:
        print(f"[전처리] 대사 정리 오류: {str(e)}")
        st.error(f"대사 정리 중 오류: {str(e)}")
        return script


def match_characters_to_scene(scene_info: dict, characters: dict) -> list:
    """장면에 등장하는 인물들을 매칭"""
    scene_characters = []
    
    # 장면의 캐스팅 정보에서 인물 이름 추출
    casting_info = scene_info.get('casting', [])
    if isinstance(casting_info, str):
        casting_names = [name.strip() for name in casting_info.split(',')]
    elif isinstance(casting_info, list):
        casting_names = casting_info
    else:
        casting_names = []
    
    # 대사와 지문에서도 인물 이름 찾기
    dialogue = scene_info.get('dialogue', '')
    narration = scene_info.get('narration', '')
    
    for character in characters.values():
        char_name = character.name
        
        # 캐스팅 정보에 있는지 확인
        if any(char_name in casting_name for casting_name in casting_names):
            scene_characters.append(character)
            continue
        
        # 대사에 등장하는지 확인
        if char_name in dialogue:
            scene_characters.append(character)
            continue
        
        # 지문에 등장하는지 확인
        if char_name in narration:
            scene_characters.append(character)
            continue
    
    return scene_characters


def run_full_automation(novel: Novel):
    """전체 자동화 실행"""
    try:
        st.info("🚀 전체 자동화를 시작합니다...")
        
        # 1단계: 등장인물 추출
        if not novel.characters:
            st.info("1️⃣ 등장인물을 추출합니다...")
            extract_characters_from_novel(novel)
        
        # 2단계: 등장인물 이미지 생성
        characters_without_images = [char for char in novel.characters.values() if not char.reference_image_url]
        if characters_without_images:
            st.info("2️⃣ 등장인물 이미지를 생성합니다...")
            generate_character_images(novel)
        
        # 3단계: 장면 분리
        if not novel.scenes:
            st.info("3️⃣ 장면을 분리합니다...")
            split_scenes_from_novel(novel)
        
        # 4단계: 장면 이미지 생성
        scenes_without_images = [scene for scene in novel.scenes.values() if not scene.image_url]
        if scenes_without_images:
            st.info("4️⃣ 장면 이미지를 생성합니다...")
            generate_scene_images(novel)
        
        st.success("🎉 전체 자동화가 완료되었습니다!")
        
    except Exception as e:
        st.error(f"❌ 전체 자동화 실패: {str(e)}")


def load_cumulative_api_usage() -> dict:
    """파일에서 누적 API 사용량을 불러옵니다."""
    usage_file = Path("data") / "api_usage.json"
    if usage_file.exists():
        try:
            with open(usage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            st.warning(f"누적 사용량 파일을 불러오는 데 실패했습니다: {e}")
            return {}
    return {}


def save_cumulative_api_usage(usage_data: dict):
    """누적 API 사용량을 파일에 저장합니다."""
    usage_file = Path("data") / "api_usage.json"
    usage_file.parent.mkdir(exist_ok=True)
    try:
        with open(usage_file, 'w', encoding='utf-8') as f:
            json.dump(usage_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        st.error(f"누적 사용량 파일을 저장하는 데 실패했습니다: {e}")


def update_and_save_cumulative_usage():
    """현재 세션의 사용량을 누적 데이터에 합산하고 저장합니다."""
    session_usage = st.session_state.get('api_usage', {})
    cumulative_usage = st.session_state.get('cumulative_api_usage', {})

    if not session_usage:
        return

    for service, s_usage in session_usage.items():
        c_service_usage = cumulative_usage.setdefault(service, {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_data_bytes': 0,
            'prompt_tokens': 0,
            'candidates_tokens': 0,
            'total_tokens': 0
        })
        for key, value in s_usage.items():
            c_service_usage[key] = c_service_usage.get(key, 0) + value

    save_cumulative_api_usage(cumulative_usage)
    
    # 합산 후 세션 사용량 초기화 및 시간 갱신
    st.session_state.api_usage = {}
    st.session_state.last_usage_save_time = time.time()
    st.toast("누적 API 사용량을 업데이트했습니다.")

if __name__ == "__main__":
    main()