"""
파일 시스템 기반 데이터 관리자
"""

import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import streamlit as st

from .models import Novel, Character, Scene, generate_uuid
from .utils import (
    get_data_directory, 
    get_novel_directory, 
    get_images_directory,
    get_backups_directory,
    ensure_directory
)


class DataManager:
    """데이터 관리 클래스"""
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else get_data_directory()
        self.novels_file = self.data_dir / "novels.json"
        ensure_directory(self.data_dir)
    
    # === 소설 관리 ===
    
    def load_novels(self) -> Dict[str, Novel]:
        """모든 소설 메타데이터 로드"""
        try:
            if not self.novels_file.exists():
                return {}
            
            with open(self.novels_file, 'r', encoding='utf-8') as f:
                novels_data = json.load(f)
            
            novels = {}
            for novel_id, novel_data in novels_data.items():
                # 상세 데이터는 개별 파일에서 로드
                novel = self._load_novel_details(novel_id)
                if novel:
                    novels[novel_id] = novel
            
            return novels
            
        except Exception as e:
            st.error(f"소설 데이터 로드 실패: {str(e)}")
            return {}
    
    def save_novels(self, novels: Dict[str, Novel]) -> bool:
        """소설 메타데이터 저장"""
        try:
            # 메타데이터만 저장 (상세 데이터는 개별 파일에 저장)
            novels_meta = {}
            for novel_id, novel in novels.items():
                novels_meta[novel_id] = {
                    'id': novel.id,
                    'title': novel.title,
                    'description': novel.description,
                    'created_at': novel.created_at.isoformat(),
                    'character_count': novel.character_count,
                    'scene_count': novel.scene_count
                }
            
            with open(self.novels_file, 'w', encoding='utf-8') as f:
                json.dump(novels_meta, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"소설 메타데이터 저장 실패: {str(e)}")
            return False
    
    def save_novel(self, novel: Novel) -> bool:
        """개별 소설의 상세 데이터 저장"""
        try:
            novel_dir = get_novel_directory(novel.id)
            
            # 대본 저장
            script_file = novel_dir / "script.txt"
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(novel.script)
            
            # 등장인물 저장
            characters_file = novel_dir / "characters.json"
            characters_data = {
                char_id: char.to_dict() 
                for char_id, char in novel.characters.items()
            }
            with open(characters_file, 'w', encoding='utf-8') as f:
                json.dump(characters_data, f, ensure_ascii=False, indent=2)
            
            # 장면 저장
            scenes_file = novel_dir / "scenes.json"
            scenes_data = {
                scene_id: scene.to_dict()
                for scene_id, scene in novel.scenes.items()
            }
            with open(scenes_file, 'w', encoding='utf-8') as f:
                json.dump(scenes_data, f, ensure_ascii=False, indent=2)
            
            # 장 저장
            chapters_file = novel_dir / "chapters.json"
            chapters_data = {
                chap_id: chap.to_dict()
                for chap_id, chap in novel.chapters.items()
            }
            with open(chapters_file, 'w', encoding='utf-8') as f:
                json.dump(chapters_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"소설 상세 데이터 저장 실패: {str(e)}")
            return False
    
    def _load_novel_details(self, novel_id: str) -> Optional[Novel]:
        """개별 소설의 상세 데이터 로드"""
        try:
            novel_dir = get_novel_directory(novel_id)
            
            # 기본 메타데이터 로드
            with open(self.novels_file, 'r', encoding='utf-8') as f:
                novels_meta = json.load(f)
            
            if novel_id not in novels_meta:
                return None
            
            meta = novels_meta[novel_id]
            
            # 소설 객체 생성
            novel = Novel(
                id=meta['id'],
                title=meta['title'],
                description=meta['description'],
                created_at=datetime.fromisoformat(meta['created_at'])
            )
            
            # 대본 로드
            script_file = novel_dir / "script.txt"
            if script_file.exists():
                with open(script_file, 'r', encoding='utf-8') as f:
                    novel.script = f.read()
            
            # 등장인물 로드
            characters_file = novel_dir / "characters.json"
            if characters_file.exists():
                with open(characters_file, 'r', encoding='utf-8') as f:
                    characters_data = json.load(f)
                    novel.characters = {
                        char_id: Character.from_dict(char_data)
                        for char_id, char_data in characters_data.items()
                    }
            
            # 장면 로드
            scenes_file = novel_dir / "scenes.json"
            if scenes_file.exists():
                with open(scenes_file, 'r', encoding='utf-8') as f:
                    scenes_data = json.load(f)
                    novel.scenes = {
                        scene_id: Scene.from_dict(scene_data)
                        for scene_id, scene_data in scenes_data.items()
                    }
            
            # 장 로드
            chapters_file = novel_dir / "chapters.json"
            if chapters_file.exists():
                with open(chapters_file, 'r', encoding='utf-8') as f:
                    chapters_data = json.load(f)
                    from .models import Chapter
                    novel.chapters = {
                        chap_id: Chapter.from_dict(chap_data)
                        for chap_id, chap_data in chapters_data.items()
                    }
            
            return novel
            
        except Exception as e:
            st.error(f"소설 상세 데이터 로드 실패 ({novel_id}): {str(e)}")
            return None
    
    def delete_novel(self, novel_id: str) -> bool:
        """소설 삭제"""
        try:
            # 소설 디렉토리 전체 삭제
            novel_dir = get_novel_directory(novel_id)
            if novel_dir.exists():
                shutil.rmtree(novel_dir)
            
            # 메타데이터에서 제거
            if self.novels_file.exists():
                with open(self.novels_file, 'r', encoding='utf-8') as f:
                    novels_meta = json.load(f)
                
                if novel_id in novels_meta:
                    del novels_meta[novel_id]
                    
                    with open(self.novels_file, 'w', encoding='utf-8') as f:
                        json.dump(novels_meta, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"소설 삭제 실패: {str(e)}")
            return False
    
    # === 이미지 관리 ===
    
    def save_character_image(self, novel_id: str, character_id: str, image_data: bytes) -> str:
        """등장인물 이미지 저장"""
        try:
            images_dir = get_images_directory(novel_id)
            image_path = images_dir / "characters" / f"{character_id}.png"
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            return str(image_path.relative_to(self.data_dir))
            
        except Exception as e:
            st.error(f"등장인물 이미지 저장 실패: {str(e)}")
            return ""
    
    def save_scene_image(self, novel_id: str, scene_id: str, image_data: bytes) -> str:
        """장면 이미지 저장"""
        try:
            images_dir = get_images_directory(novel_id)
            image_path = images_dir / "scenes" / f"{scene_id}.png"
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            return str(image_path.relative_to(self.data_dir))
            
        except Exception as e:
            st.error(f"장면 이미지 저장 실패: {str(e)}")
            return ""
    
    def load_image(self, image_path: str) -> Optional[bytes]:
        """이미지 파일 로드"""
        try:
            full_path = self.data_dir / image_path
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    return f.read()
            return None
            
        except Exception as e:
            st.error(f"이미지 로드 실패: {str(e)}")
            return None
    
    # === 내보내기/가져오기 ===
    
    def export_novel(self, novel_id: str) -> Optional[bytes]:
        """소설을 JSON 파일로 내보내기"""
        try:
            novel = self._load_novel_details(novel_id)
            if not novel:
                return None
            
            # 이미지 데이터도 포함하여 내보내기
            export_data = novel.to_dict()
            
            # 이미지를 base64로 인코딩하여 포함
            import base64
            
            for char_id, char in novel.characters.items():
                if char.reference_image_url:
                    image_data = self.load_image(char.reference_image_url)
                    if image_data:
                        export_data['characters'][char_id]['image_data'] = base64.b64encode(image_data).decode()
            
            for scene_id, scene in novel.scenes.items():
                if scene.image_url:
                    image_data = self.load_image(scene.image_url)
                    if image_data:
                        export_data['scenes'][scene_id]['image_data'] = base64.b64encode(image_data).decode()
            
            # JSON으로 직렬화
            json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
            return json_data.encode('utf-8')
            
        except Exception as e:
            st.error(f"소설 내보내기 실패: {str(e)}")
            return None
    
    def import_novel(self, file_data: bytes) -> Optional[Novel]:
        """JSON 파일에서 소설 가져오기"""
        try:
            # JSON 파싱
            json_data = json.loads(file_data.decode('utf-8'))
            
            # 새로운 ID 생성 (중복 방지)
            original_id = json_data['id']
            new_id = generate_uuid()
            json_data['id'] = new_id
            
            # 소설 객체 생성
            novel = Novel.from_dict(json_data)
            
            # 이미지 데이터 복원
            import base64
            
            for char_id, char in novel.characters.items():
                char.novel_id = new_id  # 새 소설 ID로 업데이트
                
                if 'image_data' in json_data['characters'][char_id]:
                    image_data = base64.b64decode(json_data['characters'][char_id]['image_data'])
                    image_path = self.save_character_image(new_id, char_id, image_data)
                    char.reference_image_url = image_path
            
            for scene_id, scene in novel.scenes.items():
                scene.novel_id = new_id  # 새 소설 ID로 업데이트
                
                if 'image_data' in json_data['scenes'][scene_id]:
                    image_data = base64.b64decode(json_data['scenes'][scene_id]['image_data'])
                    image_path = self.save_scene_image(new_id, scene_id, image_data)
                    scene.image_url = image_path
            
            return novel
            
        except Exception as e:
            st.error(f"소설 가져오기 실패: {str(e)}")
            return None
    
    # === 백업/복원 ===
    
    def backup_all_data(self) -> Optional[bytes]:
        """전체 데이터 백업"""
        try:
            backup_dir = get_backups_directory()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{timestamp}.zip"
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 모든 파일을 zip에 추가
                for file_path in self.data_dir.rglob('*'):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        arcname = file_path.relative_to(self.data_dir)
                        zipf.write(file_path, arcname)
            
            # 백업 파일 읽기
            with open(backup_file, 'rb') as f:
                backup_data = f.read()
            
            return backup_data
            
        except Exception as e:
            st.error(f"백업 실패: {str(e)}")
            return None
    
    def restore_from_backup(self, backup_data: bytes, overwrite: bool = False) -> bool:
        """백업에서 복원"""
        try:
            backup_dir = get_backups_directory()
            temp_backup_file = backup_dir / "temp_restore.zip"
            
            # 임시 파일로 저장
            with open(temp_backup_file, 'wb') as f:
                f.write(backup_data)
            
            # 기존 데이터 백업 (덮어쓰기가 아닌 경우)
            if not overwrite:
                existing_backup = self.backup_all_data()
                if existing_backup:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    existing_backup_file = backup_dir / f"pre_restore_backup_{timestamp}.zip"
                    with open(existing_backup_file, 'wb') as f:
                        f.write(existing_backup)
            
            # 복원 실행
            with zipfile.ZipFile(temp_backup_file, 'r') as zipf:
                zipf.extractall(self.data_dir)
            
            # 임시 파일 삭제
            temp_backup_file.unlink()
            
            return True
            
        except Exception as e:
            st.error(f"복원 실패: {str(e)}")
            return False
    
    # === 유틸리티 ===
    
    def get_storage_info(self) -> dict:
        """저장소 정보 반환"""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.data_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            novels = self.load_novels()
            
            return {
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'novel_count': len(novels),
                'total_characters': sum(novel.character_count for novel in novels.values()),
                'total_scenes': sum(novel.scene_count for novel in novels.values())
            }
            
        except Exception as e:
            st.error(f"저장소 정보 조회 실패: {str(e)}")
            return {}