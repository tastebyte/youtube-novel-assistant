# Design Document

## Overview

유튜브소설어시스트는 Streamlit 기반의 웹 애플리케이션으로, 다음과 같은 자동화된 워크플로우를 제공합니다:

**핵심 워크플로우:**
1. **소설 입력**: 사용자가 소설명과 전체 대본 텍스트를 입력
2. **등장인물 추출**: 제미나이 AI가 대본에서 등장인물을 자동 추출하고 외모 묘사 생성
3. **등장인물 이미지 생성**: 나노바나나 API로 각 등장인물의 기준 이미지 생성
4. **장면 분리**: 제미나이 AI가 전체 대본을 개별 장면(scenes)으로 자동 분할
5. **장면 이미지 생성**: 각 장면의 내용 + 등장인물 기준 이미지를 조합하여 장면별 이미지 생성

이 시스템은 소설 단위의 계층적 데이터 구조를 가지며, 등장인물의 시각적 일관성을 보장하면서 전체 소설의 시각화를 자동으로 완성합니다.

## Architecture

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Data Manager   │    │  External APIs  │
│   Frontend      │◄──►│   (JSON Files)   │    │                 │
│                 │    │                  │    │ • Gemini API    │
│ • UI Components │    │ • Novel Data     │◄──►│ • NovaNana API  │
│ • State Mgmt    │    │ • File I/O       │    │                 │
│ • Event Handlers│    │ • Backup/Restore │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow (자동화 워크플로우)
1. **소설 생성**: 사용자가 소설명 + 전체 대본 입력
2. **등장인물 추출**: 제미나이 API → 대본 분석 → 등장인물 리스트 + 외모 묘사
3. **등장인물 이미지 생성**: 나노바나나 API → 각 등장인물 기준 이미지 생성
4. **장면 분리**: 제미나이 API → 대본을 개별 장면으로 분할
5. **장면 이미지 생성**: 제미나이 API (프롬프트 생성) + 나노바나나 API (이미지 생성)
6. **데이터 저장**: 모든 결과를 JSON 파일 + 이미지 파일로 저장

## Components and Interfaces

### 1. Main Application (main.py)
```python
# Streamlit 앱의 진입점
def main():
    st.set_page_config(page_title="유튜브소설어시스트", layout="wide")
    initialize_session_state()
    render_sidebar()
    render_main_content()
```

### 2. Data Models (models.py)
```python
@dataclass
class Novel:
    id: str
    title: str
    description: str
    script: str  # 전체 대본 텍스트
    created_at: datetime
    characters: Dict[str, Character]
    scenes: Dict[str, Scene]

@dataclass
class Character:
    id: str
    novel_id: str
    name: str
    description: str
    reference_image_url: str
    created_at: datetime

@dataclass
class Scene:
    id: str
    novel_id: str
    title: str
    storyboard: str
    narration: str
    dialogue: str
    casting: List[str]  # Character IDs
    mise_en_scene: str
    image_prompt: str
    image_url: str
    created_at: datetime
```

### 3. Data Manager (data_manager.py)
```python
class DataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.novels_file = self.data_dir / "novels.json"
        
    def load_novels(self) -> Dict[str, Novel]
    def save_novels(self, novels: Dict[str, Novel])
    def save_script(self, novel_id: str, script: str)  # 대본 저장
    def load_script(self, novel_id: str) -> str        # 대본 불러오기
    def export_novel(self, novel_id: str) -> bytes
    def import_novel(self, file_data: bytes) -> Novel
    def backup_all_data(self) -> bytes
    def restore_from_backup(self, backup_data: bytes)
```

### 4. API Clients (api_clients.py)
```python
class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def extract_characters_from_script(self, script: str) -> List[Dict[str, str]]:
        """대본에서 등장인물 추출 + 외모 묘사 생성"""
        
    def split_script_into_scenes(self, script: str) -> List[Dict[str, str]]:
        """전체 대본을 개별 장면으로 분할"""
        
    def generate_scene_prompt(self, scene_data: Scene, characters: List[Character]) -> str:
        """장면 내용 + 등장인물 정보로 이미지 프롬프트 생성"""

class NovaNanaClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def generate_character_reference_image(self, character_description: str) -> bytes:
        """등장인물 외모 묘사로 기준 이미지 생성"""
        
    def generate_scene_image(self, scene_prompt: str, character_reference_images: List[bytes]) -> bytes:
        """장면 프롬프트 + 등장인물 기준 이미지들로 장면 이미지 생성"""
```

### 5. UI Components (ui_components.py)
```python
def render_novel_selector() -> str
def render_script_editor(novel_id: str)  # 대본 편집 UI
def render_character_manager(novel_id: str)
def render_scene_editor(novel_id: str, scene_id: str)
def render_image_generator(scene: Scene, characters: List[Character])
def render_file_operations()
```

## Data Models

### File Structure
```
data/
├── novels.json              # 모든 소설 메타데이터
├── novels/
│   ├── {novel_id}/
│   │   ├── script.txt       # 전체 대본 텍스트 파일
│   │   ├── characters.json  # 해당 소설의 등장인물
│   │   ├── scenes.json      # 해당 소설의 장면들
│   │   └── images/          # 생성된 이미지들
│   │       ├── characters/
│   │       │   └── {char_id}.png
│   │       └── scenes/
│   │           └── {scene_id}.png
└── backups/                 # 백업 파일들
```

### JSON Schema
```json
// novels.json
{
  "novel_id": {
    "id": "string",
    "title": "string", 
    "description": "string",
    "script": "string",  // 전체 대본 텍스트
    "created_at": "ISO datetime",
    "character_count": "number",
    "scene_count": "number"
  }
}

// characters.json
{
  "character_id": {
    "id": "string",
    "novel_id": "string",
    "name": "string",
    "description": "string",
    "reference_image_path": "string",
    "created_at": "ISO datetime"
  }
}

// scenes.json  
{
  "scene_id": {
    "id": "string",
    "novel_id": "string",
    "title": "string",
    "storyboard": "string",
    "narration": "string", 
    "dialogue": "string",
    "casting": ["character_id1", "character_id2"],
    "mise_en_scene": "string",
    "image_prompt": "string",
    "image_path": "string",
    "created_at": "ISO datetime"
  }
}
```

## Error Handling

### API Error Handling
```python
class APIError(Exception):
    def __init__(self, service: str, message: str, status_code: int = None):
        self.service = service
        self.message = message
        self.status_code = status_code

def handle_api_error(error: APIError):
    if error.service == "gemini":
        st.error(f"제미나이 API 오류: {error.message}")
        # 대안 제시 (기본 템플릿 사용)
    elif error.service == "novanana":
        st.error(f"나노바나나 API 오류: {error.message}")
        # 재시도 버튼 제공
```

### File Operation Error Handling
```python
def safe_file_operation(operation: Callable, error_message: str):
    try:
        return operation()
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {error_message}")
    except PermissionError:
        st.error(f"파일 접근 권한이 없습니다: {error_message}")
    except json.JSONDecodeError:
        st.error(f"파일 형식이 올바르지 않습니다: {error_message}")
```

## Testing Strategy

### Unit Tests
- **Data Models**: 데이터 클래스 검증
- **Data Manager**: 파일 I/O 작업 테스트
- **API Clients**: Mock API 응답 테스트
- **Utility Functions**: 이미지 처리, 파일 압축 등

### Integration Tests  
- **API Integration**: 실제 API 호출 테스트 (선택적)
- **File Operations**: 전체 저장/불러오기 워크플로우
- **Data Consistency**: 소설-캐릭터-장면 관계 무결성

### User Acceptance Tests
- **Complete Workflow**: 소설 생성 → 캐릭터 생성 → 장면 생성 → 이미지 생성
- **File Management**: 저장/불러오기/백업/복원 전체 과정
- **Error Scenarios**: 잘못된 파일, API 오류 등 예외 상황

## Performance Considerations

### Image Optimization
```python
def compress_image(image_data: bytes, quality: int = 85) -> bytes:
    # PIL을 사용한 이미지 압축
    # 메모리 사용량 최적화
    
def lazy_load_images():
    # 이미지를 필요할 때만 로드
    # Streamlit 캐싱 활용
```

### Caching Strategy
```python
@st.cache_data
def load_novel_data(novel_id: str) -> Novel:
    # 소설 데이터 캐싱
    
@st.cache_resource  
def get_api_client(service: str, api_key: str):
    # API 클라이언트 인스턴스 캐싱
```

### Memory Management
- 대용량 이미지 처리 시 스트리밍 방식 사용
- 세션 상태 최적화로 메모리 사용량 제한
- 임시 파일 자동 정리 메커니즘

## Security Considerations

### API Key Management
```python
def get_api_key(service: str) -> str:
    # 환경 변수 또는 Streamlit secrets 사용
    return st.secrets.get(f"{service}_api_key") or os.getenv(f"{service.upper()}_API_KEY")
```

### File Upload Security
- 파일 크기 제한 (최대 50MB)
- 허용된 파일 형식만 업로드 (.json, .zip)
- 파일 내용 검증 후 처리

### Data Privacy
- 로컬 파일 시스템 사용으로 데이터 외부 유출 방지
- 사용자 데이터 암호화 옵션 제공 (선택사항)## 
Automated Workflow Implementation

### 1. Novel Creation Workflow
```python
class NovelWorkflow:
    def __init__(self, gemini_client: GeminiClient, novanana_client: NovaNanaClient):
        self.gemini = gemini_client
        self.novanana = novanana_client
    
    async def create_novel_from_script(self, title: str, script: str) -> Novel:
        """전체 자동화 워크플로우 실행"""
        
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
        
        # 2. 등장인물 추출 및 이미지 생성
        characters = await self.extract_and_create_characters(novel.id, script)
        novel.characters = characters
        
        # 3. 장면 분리 및 이미지 생성  
        scenes = await self.split_and_create_scenes(novel.id, script, characters)
        novel.scenes = scenes
        
        return novel
    
    async def extract_and_create_characters(self, novel_id: str, script: str) -> Dict[str, Character]:
        """등장인물 추출 → 이미지 생성"""
        
        # 제미나이로 등장인물 추출
        character_data = self.gemini.extract_characters_from_script(script)
        
        characters = {}
        for char_info in character_data:
            # 등장인물 객체 생성
            character = Character(
                id=generate_uuid(),
                novel_id=novel_id,
                name=char_info['name'],
                description=char_info['description'],
                reference_image_url="",
                created_at=datetime.now()
            )
            
            # 나노바나나로 기준 이미지 생성
            image_data = self.novanana.generate_character_reference_image(character.description)
            image_path = save_character_image(character.id, image_data)
            character.reference_image_url = image_path
            
            characters[character.id] = character
            
        return characters
    
    async def split_and_create_scenes(self, novel_id: str, script: str, characters: Dict[str, Character]) -> Dict[str, Scene]:
        """장면 분리 → 이미지 생성"""
        
        # 제미나이로 장면 분리
        scene_data = self.gemini.split_script_into_scenes(script)
        
        scenes = {}
        for scene_info in scene_data:
            # 장면 객체 생성
            scene = Scene(
                id=generate_uuid(),
                novel_id=novel_id,
                title=scene_info['title'],
                storyboard=scene_info.get('storyboard', ''),
                narration=scene_info.get('narration', ''),
                dialogue=scene_info.get('dialogue', ''),
                casting=scene_info.get('casting', []),  # 등장인물 ID 리스트
                mise_en_scene=scene_info.get('mise_en_scene', ''),
                image_prompt="",
                image_url="",
                created_at=datetime.now()
            )
            
            # 해당 장면의 등장인물들 찾기
            scene_characters = [characters[char_id] for char_id in scene.casting if char_id in characters]
            
            # 제미나이로 장면 이미지 프롬프트 생성
            scene.image_prompt = self.gemini.generate_scene_prompt(scene, scene_characters)
            
            # 등장인물 기준 이미지들 수집
            reference_images = []
            for character in scene_characters:
                if character.reference_image_url:
                    image_data = load_image_file(character.reference_image_url)
                    reference_images.append(image_data)
            
            # 나노바나나로 장면 이미지 생성
            scene_image_data = self.novanana.generate_scene_image(scene.image_prompt, reference_images)
            scene_image_path = save_scene_image(scene.id, scene_image_data)
            scene.image_url = scene_image_path
            
            scenes[scene.id] = scene
            
        return scenes
```

### 2. Progress Tracking
```python
def show_workflow_progress(step: str, current: int, total: int):
    """워크플로우 진행 상황 표시"""
    progress = current / total
    st.progress(progress)
    st.write(f"{step}: {current}/{total}")
    
    if step == "등장인물 생성":
        st.info(f"등장인물 {current}명의 이미지를 생성 중...")
    elif step == "장면 분리":
        st.info(f"장면 {current}개를 분석 중...")
    elif step == "장면 이미지 생성":
        st.info(f"장면 {current}개의 이미지를 생성 중...")
```

### 3. Error Recovery
```python
def handle_workflow_error(step: str, error: Exception, novel_data: dict):
    """워크플로우 중 오류 발생 시 복구"""
    
    st.error(f"{step} 중 오류 발생: {str(error)}")
    
    # 부분 완성된 데이터 저장
    if novel_data:
        st.info("부분 완성된 데이터를 저장합니다...")
        save_partial_novel_data(novel_data)
        
    # 재시도 옵션 제공
    if st.button(f"{step} 재시도"):
        st.rerun()
```