"""
데이터 모델 정의
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import uuid


def generate_uuid() -> str:
    """고유 ID 생성"""
    return str(uuid.uuid4())


@dataclass
class Chapter:
    """장(Chapter) 데이터 모델"""
    id: str
    novel_id: str
    chapter_number: int
    title: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'novel_id': self.novel_id,
            'chapter_number': self.chapter_number,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Chapter':
        """딕셔너리에서 생성"""
        return cls(
            id=data['id'],
            novel_id=data['novel_id'],
            chapter_number=data['chapter_number'],
            title=data['title'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class Character:
    """등장인물 데이터 모델"""
    id: str
    novel_id: str
    name: str
    description: str
    reference_image_url: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'novel_id': self.novel_id,
            'name': self.name,
            'description': self.description,
            'reference_image_url': self.reference_image_url,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        """딕셔너리에서 생성"""
        return cls(
            id=data['id'],
            novel_id=data['novel_id'],
            name=data['name'],
            description=data['description'],
            reference_image_url=data.get('reference_image_url', ''),
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class Scene:
    """장면 데이터 모델"""
    id: str
    novel_id: str
    chapter_id: str = ""  # 소속 장 ID
    title: str = ""
    storyboard: str = ""
    narration: str = ""
    dialogue: str = ""
    casting: List[str] = field(default_factory=list)  # Character IDs
    mise_en_scene: str = ""
    image_prompt: str = ""
    image_url: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'novel_id': self.novel_id,
            'chapter_id': self.chapter_id,
            'title': self.title,
            'storyboard': self.storyboard,
            'narration': self.narration,
            'dialogue': self.dialogue,
            'casting': self.casting,
            'mise_en_scene': self.mise_en_scene,
            'image_prompt': self.image_prompt,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Scene':
        """딕셔너리에서 생성"""
        return cls(
            id=data['id'],
            novel_id=data['novel_id'],
            chapter_id=data.get('chapter_id', ''),
            title=data['title'],
            storyboard=data.get('storyboard', ''),
            narration=data.get('narration', ''),
            dialogue=data.get('dialogue', ''),
            casting=data.get('casting', []),
            mise_en_scene=data.get('mise_en_scene', ''),
            image_prompt=data.get('image_prompt', ''),
            image_url=data.get('image_url', ''),
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class Novel:
    """소설 데이터 모델"""
    id: str
    title: str
    description: str = ""
    script: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    characters: Dict[str, Character] = field(default_factory=dict)
    scenes: Dict[str, Scene] = field(default_factory=dict)
    chapters: Dict[str, Chapter] = field(default_factory=dict)
    
    @property
    def character_count(self) -> int:
        """등장인물 수"""
        return len(self.characters)
    
    @property
    def scene_count(self) -> int:
        """장면 수"""
        return len(self.scenes)
    
    @property
    def chapter_count(self) -> int:
        """장 수"""
        return len(self.chapters)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'script': self.script,
            'created_at': self.created_at.isoformat(),
            'character_count': self.character_count,
            'scene_count': self.scene_count,
            'chapter_count': self.chapter_count,
            'characters': {char_id: char.to_dict() for char_id, char in self.characters.items()},
            'scenes': {scene_id: scene.to_dict() for scene_id, scene in self.scenes.items()},
            'chapters': {chap_id: chap.to_dict() for chap_id, chap in self.chapters.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Novel':
        """딕셔너리에서 생성"""
        novel = cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            script=data.get('script', ''),
            created_at=datetime.fromisoformat(data['created_at'])
        )
        
        # 등장인물 복원
        if 'characters' in data:
            novel.characters = {
                char_id: Character.from_dict(char_data)
                for char_id, char_data in data['characters'].items()
            }
        
        # 장면 복원
        if 'scenes' in data:
            novel.scenes = {
                scene_id: Scene.from_dict(scene_data)
                for scene_id, scene_data in data['scenes'].items()
            }
        
        # 장 복원
        if 'chapters' in data:
            novel.chapters = {
                chap_id: Chapter.from_dict(chap_data)
                for chap_id, chap_data in data['chapters'].items()
            }
        
        return novel