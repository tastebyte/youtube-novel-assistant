"""
자동화 워크플로우 엔진
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import time

from .models import Novel, Character, Scene, generate_uuid
from .api_clients import GeminiClient, GeminiImageClient
from .data_manager import DataManager
from .utils import get_api_key, validate_api_keys
from .image_utils import compress_image, optimize_for_web


class NovelWorkflow:
    """소설 자동화 워크플로우 엔진"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.image_client = GeminiImageClient()
        self.data_manager = DataManager()
        
        # API 키 검증
        api_validation = validate_api_keys()
        if not api_validation['valid']:
            st.error(f"API 키가 설정되지 않았습니다: {', '.join(api_validation['missing_keys'])}")
    
    def create_novel_from_script(self, title: str, script: str) -> Optional[Novel]:
        """전체 자동화 워크플로우 실행"""
        try:
            # 1. 소설 기본 정보 생성
            novel = Novel(
                id=generate_uuid(),
                title=title,
                script=script,
                description="",
                created_at=datetime.now(),
                characters={},
                scenes={}
            )
            
            st.info("🚀 자동화 워크플로우를 시작합니다...")
            
            # 진행 상황 표시를 위한 컨테이너
            progress_container = st.container()
            
            with progress_container:
                # 2. 등장인물 추출 및 이미지 생성
                st.info("👥 등장인물을 추출하고 이미지를 생성합니다...")
                characters = self.extract_and_create_characters(novel.id, script)
                if characters:
                    novel.characters = characters
                    st.success(f"✅ {len(characters)}명의 등장인물이 생성되었습니다.")
                else:
                    st.warning("⚠️ 등장인물 생성에 실패했습니다.")
                
                # 3. 장면 분리 및 이미지 생성
                st.info("🎬 장면을 분리하고 이미지를 생성합니다...")
                scenes = self.split_and_create_scenes(novel.id, script, characters)
                if scenes:
                    novel.scenes = scenes
                    st.success(f"✅ {len(scenes)}개의 장면이 생성되었습니다.")
                else:
                    st.warning("⚠️ 장면 생성에 실패했습니다.")
            
            # 4. 데이터 저장
            if self.data_manager.save_novel(novel):
                # 메타데이터도 업데이트
                novels = self.data_manager.load_novels()
                novels[novel.id] = novel
                self.data_manager.save_novels(novels)
                
                st.success("🎉 소설이 성공적으로 생성되었습니다!")
                return novel
            else:
                st.error("❌ 소설 저장에 실패했습니다.")
                return None
                
        except Exception as e:
            st.error(f"❌ 워크플로우 실행 중 오류 발생: {str(e)}")
            return None
    
    def extract_and_create_characters(self, novel_id: str, script: str) -> Dict[str, Character]:
        """등장인물 추출 → 이미지 생성"""
        try:
            # 제미나이로 등장인물 추출
            character_data = self.gemini_client.extract_characters_from_script(script)
            
            if not character_data:
                st.error("등장인물을 추출할 수 없습니다.")
                return {}
            
            characters = {}
            total_chars = len(character_data)
            
            # 진행률 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, char_info in enumerate(character_data):
                try:
                    # 등장인물 객체 생성
                    character = Character(
                        id=generate_uuid(),
                        novel_id=novel_id,
                        name=char_info['name'],
                        description=char_info['description'],
                        reference_image_url="",
                        created_at=datetime.now()
                    )
                    
                    # 진행 상황 업데이트
                    progress = (i + 1) / total_chars
                    progress_bar.progress(progress)
                    status_text.text(f"등장인물 이미지 생성 중: {character.name} ({i+1}/{total_chars})")
                    
                    # 이미지 생성
                    image_data = self.image_client.generate_character_reference_image(character.description)
                    if image_data:
                        image_path = self.data_manager.save_character_image(novel_id, character.id, image_data)
                        character.reference_image_url = image_path
                    
                    characters[character.id] = character
                    
                    # API 호출 간격 조절
                    time.sleep(1)
                    
                except Exception as e:
                    st.warning(f"등장인물 '{char_info.get('name', 'Unknown')}' 처리 중 오류: {str(e)}")
                    continue
            
            progress_bar.empty()
            status_text.empty()
            
            return characters
            
        except Exception as e:
            st.error(f"등장인물 추출 실패: {str(e)}")
            return {}
    
    def split_and_create_scenes(self, novel_id: str, script: str, characters: Dict[str, Character]) -> Dict[str, Scene]:
        """장면 분리 → 이미지 생성"""
        try:
            # 제미나이로 장면 분리
            scene_data = self.gemini_client.split_script_into_scenes(script)
            
            if not scene_data:
                st.error("장면을 분리할 수 없습니다.")
                return {}
            
            scenes = {}
            total_scenes = len(scene_data)
            
            # 진행률 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, scene_info in enumerate(scene_data):
                try:
                    # 장면 객체 생성
                    scene = Scene(
                        id=generate_uuid(),
                        novel_id=novel_id,
                        title=scene_info.get('title', f'장면 {i+1}'),
                        storyboard=scene_info.get('storyboard', ''),
                        narration=scene_info.get('narration', ''),
                        dialogue=scene_info.get('dialogue', ''),
                        casting=[],  # 나중에 매칭
                        mise_en_scene=scene_info.get('mise_en_scene', ''),
                        image_prompt="",
                        image_url="",
                        created_at=datetime.now()
                    )
                    
                    # 진행 상황 업데이트
                    progress = (i + 1) / total_scenes
                    progress_bar.progress(progress)
                    status_text.text(f"장면 이미지 생성 중: {scene.title} ({i+1}/{total_scenes})")
                    
                    # 등장인물 매칭
                    scene_characters = self._match_characters_to_scene(scene_info, characters)
                    scene.casting = [char.id for char in scene_characters]
                    
                    # 이미지 프롬프트 생성
                    scene.image_prompt = self.gemini_client.generate_scene_prompt(scene, scene_characters)
                    
                    # 장면 이미지 생성
                    reference_images = []
                    for character in scene_characters:
                        if character.reference_image_url:
                            image_data = self.data_manager.load_image(character.reference_image_url)
                            if image_data:
                                reference_images.append(image_data)
                    
                    scene_image_data = self.image_client.generate_scene_image(scene.image_prompt, reference_images)
                    if scene_image_data:
                        scene_image_path = self.data_manager.save_scene_image(novel_id, scene.id, scene_image_data)
                        scene.image_url = scene_image_path
                    
                    scenes[scene.id] = scene
                    
                    # API 호출 간격 조절
                    time.sleep(1)
                    
                except Exception as e:
                    st.warning(f"장면 '{scene_info.get('title', 'Unknown')}' 처리 중 오류: {str(e)}")
                    continue
            
            progress_bar.empty()
            status_text.empty()
            
            return scenes
            
        except Exception as e:
            st.error(f"장면 분리 실패: {str(e)}")
            return {}
    
    def _match_characters_to_scene(self, scene_info: dict, characters: Dict[str, Character]) -> List[Character]:
        """장면에 등장하는 인물들을 매칭"""
        scene_characters = []
        
        # 장면의 캐스팅 정보에서 인물 이름 추출
        casting_info = scene_info.get('casting', [])
        if isinstance(casting_info, str):
            # 문자열인 경우 쉼표로 분리
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
    
    def show_workflow_progress(self, step: str, current: int, total: int):
        """워크플로우 진행 상황 표시"""
        progress = current / total if total > 0 else 0
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.progress(progress)
        
        with col2:
            st.write(f"{current}/{total}")
        
        if step == "등장인물 생성":
            st.info(f"등장인물 {current}명의 이미지를 생성 중...")
        elif step == "장면 분리":
            st.info(f"장면 {current}개를 분석 중...")
        elif step == "장면 이미지 생성":
            st.info(f"장면 {current}개의 이미지를 생성 중...")
    
    def handle_workflow_error(self, step: str, error: Exception, novel_data: Optional[dict] = None):
        """워크플로우 중 오류 발생 시 복구"""
        st.error(f"{step} 중 오류 발생: {str(error)}")
        
        # 부분 완성된 데이터 저장
        if novel_data:
            st.info("부분 완성된 데이터를 저장합니다...")
            try:
                # 임시 저장 로직
                temp_novel = Novel.from_dict(novel_data)
                if self.data_manager.save_novel(temp_novel):
                    st.success("부분 데이터가 저장되었습니다.")
            except Exception as save_error:
                st.error(f"부분 데이터 저장 실패: {str(save_error)}")
        
        # 재시도 옵션 제공
        if st.button(f"{step} 재시도", key=f"retry_{step}"):
            st.rerun()


class WorkflowManager:
    """워크플로우 관리자 (Streamlit 세션 상태 통합)"""
    
    def __init__(self):
        if 'workflow' not in st.session_state:
            st.session_state.workflow = NovelWorkflow()
        
        self.workflow = st.session_state.workflow
    
    def create_novel_with_progress(self, title: str, script: str) -> Optional[Novel]:
        """진행 상황을 표시하면서 소설 생성"""
        return self.workflow.create_novel_from_script(title, script)
    
    def get_workflow_status(self) -> dict:
        """현재 워크플로우 상태 반환"""
        return {
            'api_keys_valid': validate_api_keys()['valid'],
            'gemini_available': self.workflow.gemini_client.api_key is not None,
            'image_available': self.workflow.image_client.api_key is not None
        }