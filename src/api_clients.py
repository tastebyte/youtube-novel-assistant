"""
API 클라이언트 구현
"""
import json
import requests
import time
from typing import List, Dict, Optional, Any
from .models import Scene, Character
from .utils import get_api_key
from .security import SecureAPIClient, log_api_usage


import streamlit as st


class GeminiClient(SecureAPIClient):
    def _log_request(self, endpoint: str, success: bool, response_size: int, usage_metadata: Optional[Dict[str, int]] = None):
        """API 요청 로깅 및 사용량 집계"""
        service = self.service_name
        
        if service not in st.session_state.api_usage:
            st.session_state.api_usage[service] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_data_bytes': 0,
                'prompt_tokens': 0,
                'candidates_tokens': 0,
                'total_tokens': 0
            }
        
        usage = st.session_state.api_usage[service]
        usage['total_requests'] += 1
        usage['total_data_bytes'] += response_size
        if success:
            usage['successful_requests'] += 1
            if usage_metadata:
                usage['prompt_tokens'] += usage_metadata.get('promptTokenCount', 0)
                usage['candidates_tokens'] += usage_metadata.get('candidatesTokenCount', 0)
                usage['total_tokens'] += usage_metadata.get('totalTokenCount', 0)
        else:
            usage['failed_requests'] += 1
    """제미나이 API 클라이언트 (텍스트 분석용) - 보안 강화"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__('gemini')
        if api_key:
            self.api_key = api_key
        
        if not self.api_key:
            st.error("제미나이 API 키가 설정되지 않았습니다. .env 파일 또는 Streamlit secrets를 확인해주세요.")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        # 텍스트 분석 및 생성 모델 업데이트
        self.text_model = "gemini-2.5-flash-preview-05-20"
    
    def test_api_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            print("[제미나이 API] 연결 테스트 시작")
            test_prompt = "안녕하세요. 간단한 테스트입니다."
            
            response = self._make_request(test_prompt, max_retries=1)
            
            if response:
                print("[제미나이 API] ✅ 연결 테스트 성공")
                return True
            else:
                print("[제미나이 API] ❌ 연결 테스트 실패")
                return False
                
        except Exception as e:
            print(f"[제미나이 API] ❌ 연결 테스트 오류: {str(e)}")
            return False
    
    def _make_request(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """제미나이 텍스트 API 요청 (보안 강화 + 재시도 로직)"""
        if not self.api_key:
            st.error("❌ API 키가 설정되지 않았습니다.")
            return None
        
        print(f"[제미나이 API] 요청 시작 - 프롬프트 길이: {len(prompt)} 문자")
        print(f"[제미나이 API] 사용 모델: {self.text_model}")
        # 프롬프트가 너무 길 수 있으므로 앞 500자만 표시
        print(f"[제미나이 API] 전송 프롬프트 (일부): {prompt[:500]}...")
        print("-" * 20)
        
        # 프롬프트 길이 체크
        if len(prompt) > 30000:
            st.warning(f"⚠️ 프롬프트가 매우 깁니다 ({len(prompt)} 문자). 타임아웃 위험이 있습니다.")
        elif len(prompt) > 15000:
            st.info(f"ℹ️ 프롬프트가 깁니다 ({len(prompt)} 문자). 처리 시간이 오래 걸릴 수 있습니다.")
        
        for attempt in range(max_retries):
            try:
                # 요청 빈도 제한 확인 (더 엄격하게)
                if not self._check_rate_limit():
                    if attempt < max_retries - 1:
                        import time
                        st.info(f"⏳ API 요청 제한으로 {3}초 대기 중... (시도 {attempt + 1}/{max_retries})")
                        time.sleep(3)
                        continue
                    return None
                
                # 보안을 위해 API 키를 헤더로 전송
                api_url = f"{self.base_url}/{self.text_model}:generateContent"
                
                headers = {
                    'Content-Type': 'application/json',
                    'x-goog-api-key': self.api_key  # 헤더로 API 키 전송
                }
                
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }]
                }
                
                # 로그용 페이로드 생성 (프롬프트 내용 축약)
                log_payload = json.loads(json.dumps(payload))
                log_payload['contents'][0]['parts'][0]['text'] = f"{prompt[:200]}..."
                print(f"[제미나이 API] 전송 페이로드 (일부): {json.dumps(log_payload, ensure_ascii=False, indent=2)}")

                print(f"[제미나이 API] HTTP 요청 전송 중... (시도 {attempt + 1}/{max_retries})")
                print(f"[제미나이 API] 서버 응답 대기 중... (최대 60초)")
                print(f"[제미나이 API] 요청 URL: {api_url}")
                print(f"[제미나이 API] 페이로드 크기: {len(str(payload))} 바이트")
                
                import time
                start_time = time.time()
                
                print(f"[제미나이 API] 프롬프트 길이에 따른 동적 타임아웃 설정")
                if len(prompt) > 20000:
                    timeout_seconds = 120  # 2분
                elif len(prompt) > 10000:
                    timeout_seconds = 90   # 1.5분
                else:
                    timeout_seconds = 60   # 1분
                
                print(f"[제미나이 API] 타임아웃 설정: {timeout_seconds}초")
                
                try:
                    response = requests.post(api_url, headers=headers, json=payload, timeout=timeout_seconds)
                    elapsed_time = time.time() - start_time
                    print(f"[제미나이 API] 응답 시간: {elapsed_time:.2f}초")
                except requests.exceptions.Timeout:
                    elapsed_time = time.time() - start_time
                    print(f"[제미나이 API] ❌ 타임아웃 발생 - 경과 시간: {elapsed_time:.2f}초 (제한: {timeout_seconds}초)")
                    raise
                response_text = response.text
                
                print(f"[제미나이 API] ✅ 응답 수신 완료 - 상태코드: {response.status_code}, 응답 길이: {len(response_text)} 문자")
                # 500번대 서버 오류 시에도 재시도하도록 로직 추가
                if response.status_code == 429 or response.status_code >= 500:  # Too Many Requests or Server Error
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 5초, 10초, 15초 대기
                        st.warning(f"⏳ API 서버 오류({response.status_code}). {wait_time}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        st.error(f"❌ API 서버가 응답하지 않습니다({response.status_code}). 잠시 후 다시 시도해주세요.")
                        # 실패 로깅
                        self._log_request('generateContent', False, len(response_text))
                        return None
                
                if not response.ok:
                    error_message = f"API Error ({response.status_code})"
                    if response_text:
                        try:
                            error_json = response.json()
                            error_message = f"API Error ({response.status_code}): {error_json.get('error', {}).get('message', '')}"
                        except:
                            error_message += f": {response_text}"
                    
                    st.error(error_message)
                    # 실패 로깅
                    self._log_request('generateContent', False, len(response_text))
                    return None
                
                if not response_text:
                    st.warning("API returned an empty response body. This might be due to safety settings.")
                    # 실패 로깅 (내용이 없으므로)
                    self._log_request('generateContent', False, 0)
                    return None
                
                try:
                    result = response.json()
                    usage_metadata = result.get('usageMetadata', {})
                    # 성공 로깅 (토큰 정보 포함)
                    self._log_request('generateContent', True, len(response_text), usage_metadata)

                    if 'candidates' in result and len(result['candidates']) > 0:
                        content = result['candidates'][0].get('content', {})
                        parts = content.get('parts', [])
                        if parts:
                            return parts[0].get('text', '')
                    return None
                except json.JSONDecodeError:
                    st.error("Failed to parse API response")
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"[제미나이 API] 타임아웃 발생 - 시도 {attempt + 1}/{max_retries}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 15  # 15초, 30초, 45초 대기
                    st.warning(f"⏳ API 요청 타임아웃. {wait_time}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                    
                    # 타임아웃 원인 분석 메시지
                    if len(prompt) > 20000:
                        st.info("💡 프롬프트가 너무 길어서 타임아웃이 발생했을 수 있습니다. 내용을 줄여보세요.")
                    elif attempt == 0:
                        st.info("💡 네트워크 연결이 느리거나 서버가 바쁠 수 있습니다.")
                    
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    # 최종 실패 시 상세한 진단 정보 제공
                    st.error("❌ API 요청이 계속 타임아웃됩니다.")
                    
                    with st.expander("🔍 타임아웃 원인 분석"):
                        st.markdown(f"""
                        **가능한 원인들:**
                        1. **프롬프트 길이**: {len(prompt):,} 문자 (권장: 15,000자 이하)
                        2. **네트워크 연결**: 인터넷 연결 상태 확인 필요
                        3. **API 서버 상태**: 제미나이 서버가 과부하 상태일 수 있음
                        4. **API 키 문제**: API 키 유효성 또는 할당량 문제
                        
                        **해결 방법:**
                        - 대본을 더 작은 단위로 나누어 처리
                        - 잠시 후 다시 시도
                        - 네트워크 연결 상태 확인
                        - API 키 및 할당량 확인
                        """)
                    
                    return None
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 5초, 10초, 15초 대기
                    st.warning(f"⏳ 네트워크 연결 오류. {wait_time}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    st.error("❌ 네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.")
                    return None
            except Exception as e:
                st.error(f"제미나이 API 요청 실패: {str(e)}")
                return None
        
        return None
    
    def extract_characters_from_script(self, script: str) -> List[Dict[str, str]]:
        """대본에서 등장인물 추출 + 외모 묘사 생성"""
        prompt = f"""
다음은 유튜브 소설의 전체 대본입니다. 이 대본을 읽고 주요 등장인물들을 모두 추출해주세요.

[대본 시작]
{script}
[대본 끝]

각 등장인물에 대해 다음 작업을 수행해주세요:
1. 인물의 이름을 식별합니다.
2. 대본에 묘사된 외모, 나이, 성격, 의상 등의 특징을 모두 종합하여 상세한 '외모 및 특징 묘사'를 작성합니다. 
3. 이 묘사는 나중에 AI 이미지 생성 모델이 인물의 이미지를 그리는 데 사용될 것이므로, 매우 구체적이고 시각적이어야 합니다.

결과를 반드시 다음 JSON 배열(Array) 형식으로 반환해야 합니다. 각 인물 객체는 "name"과 "description" 키를 가져야 합니다.

JSON 출력 예시:
[
  {{
    "name": "박서준",
    "description": "20대 후반의 남자. 날카로운 턱선과 깊은 눈매를 가졌다. 항상 검은색 터틀넥과 긴 코트를 입고 다니며, 차가운 도시의 분위기를 풍긴다. 머리는 약간 흐트러져 있고, 무표정한 얼굴 뒤에 비밀을 숨기고 있는 듯하다."
  }},
  {{
    "name": "이하나",
    "description": "20대 중반의 여자. 밝은 갈색의 긴 생머리를 가지고 있으며, 큰 눈망울이 인상적이다. 따뜻한 미소를 짓고 있으며, 파스텔 톤의 니트와 청바지를 즐겨 입는다. 긍정적이고 활발한 성격이다."
  }}
]

반드시 유효한 JSON 형식으로만 응답해주세요.
"""
        
        try:
            response = self._make_request(prompt)
            if not response:
                return []
            
            # JSON 추출
            json_match = self._extract_json_from_response(response)
            if not json_match:
                st.error("제미나이 응답에서 유효한 JSON을 찾을 수 없습니다.")
                return []
            
            characters = json.loads(json_match)
            
            if not isinstance(characters, list):
                st.error("제미나이가 유효한 등장인물 배열을 반환하지 않았습니다.")
                return []
            
            return characters
            
        except json.JSONDecodeError as e:
            st.error(f"제미나이 응답 JSON 파싱 오류: {str(e)}")
            return []
        except Exception as e:
            st.error(f"등장인물 추출 실패: {str(e)}")
            return []
    
    def _optimize_prompt_length(self, script: str) -> str:
        """프롬프트 길이 최적화"""
        if len(script) <= 15000:
            return script
        
        print(f"[제미나이 API] 프롬프트 길이 최적화 - 원본: {len(script)} 문자")
        
        # 긴 대본을 줄이는 전략
        lines = script.split('\n')
        
        # 1. 빈 줄 제거
        lines = [line for line in lines if line.strip()]
        
        # 2. 연속된 공백 제거
        import re
        optimized_script = '\n'.join(lines)
        optimized_script = re.sub(r' +', ' ', optimized_script)
        
        # 3. 여전히 길면 앞부분만 사용 (경고와 함께)
        if len(optimized_script) > 15000:
            optimized_script = optimized_script[:15000]
            st.warning("⚠️ 대본이 너무 길어서 앞부분만 처리합니다. 전체 처리를 원하면 장으로 나누어 처리하세요.")
            print(f"[제미나이 API] 대본 잘림 - 최종 길이: {len(optimized_script)} 문자")
        
        return optimized_script
    
    def split_script_into_scenes(self, script: str) -> List[Dict[str, str]]:
        """전체 대본을 개별 장면으로 분할"""
        print(f"[장면 분리] 시작 - 대본 길이: {len(script)} 문자")
        
        # 대본이 너무 길면 분할 처리
        if len(script) > 15000:
            print(f"[장면 분리] 대본이 너무 깁니다 ({len(script)} 문자). 분할 처리를 권장합니다.")
            st.warning(f"⚠️ 대본이 매우 깁니다 ({len(script)} 문자). 처리 시간이 오래 걸릴 수 있습니다.")
        elif len(script) > 8000:
            print(f"[장면 분리] 대본이 깁니다 ({len(script)} 문자). 처리 시간이 다소 걸릴 수 있습니다.")
        
        print(f"[장면 분리] 제미나이 API로 장면 분석 요청 중...")
        
        # 프롬프트 길이 최적화
        optimized_script = self._optimize_prompt_length(script)
        
        prompt = f"""다음 대본을 장면별로 분리하여 JSON 배열로 반환하세요.

대본:
{optimized_script}

각 장면은 다음 형식으로 작성:
[{{"title":"장면제목", "narration":"지문", "dialogue":"대사", "casting":["인물1","인물2"], "storyboard":"구도설명", "mise_en_scene":"분위기"}}]

빈 필드는 ""로 처리. JSON만 반환하세요."""
        
        try:
            response = self._make_request(prompt)
            if not response:
                print("[장면 분리] 제미나이 API 응답 없음")
                return []
            
            print(f"[장면 분리] 제미나이 응답 수신 완료 - 응답 길이: {len(response)} 문자")
            print("[장면 분리] JSON 데이터 추출 중...")
            
            # JSON 추출
            json_match = self._extract_json_from_response(response)
            if not json_match:
                print("[장면 분리] JSON 추출 실패 - 응답에서 유효한 JSON을 찾을 수 없음")
                st.error("제미나이 응답에서 유효한 JSON을 찾을 수 없습니다.")
                return []
            
            print(f"[장면 분리] JSON 추출 성공 - JSON 길이: {len(json_match)} 문자")
            print("[장면 분리] JSON 파싱 중...")
            
            scenes = json.loads(json_match)
            
            if not isinstance(scenes, list):
                print(f"[장면 분리] JSON 파싱 오류 - 배열이 아닌 타입: {type(scenes)}")
                st.error("제미나이가 유효한 장면 배열을 반환하지 않았습니다.")
                return []
            
            print(f"[장면 분리] 성공 - {len(scenes)}개 장면 추출 완료")
            for i, scene in enumerate(scenes):
                print(f"  장면 {i+1}: {scene.get('title', '제목 없음')}")
            
            return scenes
            
        except json.JSONDecodeError as e:
            print(f"[장면 분리] JSON 파싱 오류: {str(e)}")
            st.error(f"제미나이 응답 JSON 파싱 오류: {str(e)}")
            return []
        except Exception as e:
            print(f"[장면 분리] 예외 발생: {str(e)}")
            st.error(f"장면 분리 실패: {str(e)}")
            return []
    
    def generate_scene_prompt(self, scene: Scene, characters: List[Character]) -> dict:
        """장면 내용 + 등장인물 정보로 이미지 프롬프트 생성"""
        # 등장인물 정보 구성
        character_info = ""
        if characters:
            character_descriptions = []
            for char in characters:
                character_descriptions.append(f"- {char.name}: {char.description}")
            character_info = "\n".join(character_descriptions)
        
        prompt = f"""
### 지시
당신은 제공된 장면과 인물 정보를 바탕으로 이미지 생성 프롬프트를 만드는 AI입니다.
각 항목에 대해 가장 핵심적인 키워드와 구문 위주로 간결하게 묘사하세요.
결과는 반드시 아래 JSON 형식으로만 반환해야 합니다.

### 장면 정보
- **제목**: {scene.title}
- **상황/지문**: {scene.narration or '없음'}
- **구도/미장센**: {scene.storyboard or ''}, {scene.mise_en_scene or ''}
- **대사**: {scene.dialogue or '없음'}

### 등장인물 정보
{character_info or '없음'}

### 출력 형식 (JSON)
```json
{{{{
  "characters": "인물의 외모, 표정, 행동을 핵심만 묘사. (예: 피곤한 표정의 20대 남성, 카운터에 기댐)",
  "background": "배경과 핵심 소품을 간결하게 묘사. (예: 늦은 밤 편의점 내부, 가지런히 정리된 선반)",
  "angle_and_composition": "카메라 앵글과 구도. (예: 미디엄 샷, 카운터 너머에서 촬영)",
  "lighting_and_color": "조명과 색감. (예: 차가운 형광등, 푸른 톤)",
  "mood_and_atmosphere": "장면의 분위기. (예: 조용함, 정적, 외로움)",
  "style": "하이퍼리얼리즘, 시네마틱, 필름 그레인, 4k, 사실적 묘사, 16:9 비율"
}}}}
```
"""
        
        try:
            response = self._make_request(prompt)
            if not response:
                # 기본 템플릿 사용
                return self._generate_default_prompt(scene, characters)
            
            # JSON 추출 및 반환
            json_match = self._extract_json_from_response(response, is_single_object=True)
            if json_match:
                return json.loads(json_match)
            
            st.warning("AI가 구조화된 프롬프트를 생성하지 못했습니다. 기본 프롬프트를 사용합니다.")
            return self._generate_default_prompt(scene, characters)
            
        except Exception as e:
            st.error(f"장면 프롬프트 생성 실패: {str(e)}")
            return self._generate_default_prompt(scene, characters)
    
    def _extract_json_from_response(self, response: str, is_single_object: bool = False) -> Optional[str]:
        """응답에서 JSON 부분 추출"""
        try:
            import re
            
            if is_single_object:
                # 단일 JSON 객체 찾기 (코드 블록 ```json ... ``` 고려)
                code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                if code_block_match:
                    return code_block_match.group(1)
                obj_match = re.search(r'(\{.*?\})', response, re.DOTALL)
                if obj_match:
                    return obj_match.group(0)
            else:
                # JSON 배열 찾기 (코드 블록 ```json ... ``` 고려)
                code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response, re.DOTALL)
                if code_block_match:
                    return code_block_match.group(1)
                # 코드 블록이 없으면 순수 JSON 배열 찾기
                array_match = re.search(r'(\[.*?\])', response, re.DOTALL)
                if array_match:
                    return array_match.group(1)
                # 배열을 못찾으면, 중괄호 객체들을 찾아서 배열로 만듦
                obj_matches = re.findall(r'\{.*?\}', response, re.DOTALL)
                if not obj_matches:
                    return None
    
                # 3. 찾은 객체들을 쉼표로 연결하여 올바른 JSON 배열 문자열을 생성
                return f"[{','.join(obj_matches)}]"
        except Exception as e:
            print(f"[JSON 추출 오류] {e}")
            return None
    
    def _generate_default_prompt(self, scene: Scene, characters: List[Character]) -> dict:
        """기본 프롬프트 템플릿"""
        character_names = [char.name for char in characters] if characters else []
        
        return {
            "characters": f"등장인물: {', '.join(character_names) if character_names else '없음'}. {scene.dialogue or ''}",
            "background": scene.narration or "장면에 대한 배경 설명",
            "angle_and_composition": "미디엄 샷",
            "lighting_and_color": "자연광",
            "mood_and_atmosphere": scene.mise_en_scene or "장면의 분위기",
            "style": "하이퍼리얼리즘, 시네마틱, 4k, 사실적 묘사, 16:9 비율"
        }


class GeminiImageClient(GeminiClient):
    """제미나이 이미지 생성 API 클라이언트 (GeminiClient 상속)"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)  # 부모 클래스의 __init__ 호출
        # 이미지 생성 모델을 'gemini-2.5-flash-image-preview'로 변경
        self.image_model = "gemini-2.5-flash-image-preview"
    
    def generate_character_reference_image(self, prompt: str) -> Optional[bytes]:
        """주어진 프롬프트로 기준 이미지 생성"""
        if not self.api_key:
            return None
        return self._generate_image(prompt)
    
    def generate_scene_image(self, scene_prompt: str, character_reference_images: List[bytes]) -> Optional[bytes]:
        """장면 프롬프트 + 등장인물 기준 이미지들로 장면 이미지 생성"""
        if not self.api_key:
            return None

        # 기준 이미지가 있으면 함께 전송
        return self._generate_image(scene_prompt, character_reference_images)
    
    def _generate_image(self, prompt: str, reference_images: Optional[List[bytes]] = None) -> Optional[bytes]:
        """
        제미나이 멀티모달 API를 사용하여 이미지 생성.
        """
        try:
            # Gemini API의 표준 콘텐츠 생성 엔드포인트 사용
            api_url = f"{self.base_url}/{self.image_model}:generateContent"
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': self.api_key
            }

            # 요청 페이로드 구성 (텍스트 + 이미지)
            parts = [{"text": prompt}]            
            if reference_images:
                import base64
                for img_data in reference_images:
                    if img_data:
                        b64_data = base64.b64encode(img_data).decode()
                        parts.append({
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": b64_data
                            }
                        })

            payload = {
                "contents": [{"parts": parts}],
                # 이미지 생성을 위한 필수 설정
                "generationConfig": {
                    "responseModalities": ["IMAGE"], # 이미지 모드로 응답 요청
                    "temperature": 0.4,
                    "topP": 1,
                    "topK": 32,
                }
            }
            
            # 로그용 페이로드 생성 (프롬프트 축약)
            log_payload = {
                "contents": [{"parts": [
                    {"text": f"{prompt[:200]}..."},
                    f"<{len(reference_images) if reference_images else 0}개의 기준 이미지 데이터>"
                ]}],
                "generationConfig": payload["generationConfig"]
            }
            print(f"[이미지 생성 API] 전송 페이로드 (일부): {json.dumps(log_payload, ensure_ascii=False, indent=2)}")
            print(f"[이미지 생성 API] 요청 시작 - 프롬프트 길이: {len(prompt)}, 기준 이미지: {len(reference_images) if reference_images else 0}개")
            print(f"[이미지 생성 API] 사용 모델: {self.image_model}")
            # 프롬프트가 너무 길 수 있으므로 앞 500자만 표시
            print(f"[이미지 생성 API] 전송 프롬프트 (일부): {prompt[:500]}...")
            print("-" * 20)
            response = requests.post(api_url, headers=headers, json=payload, timeout=90)

            if response.ok:
                result = response.json()
                usage_metadata = result.get('usageMetadata', {})
                
                # Gemini API의 표준 응답 형식에 맞게 수정
                if 'candidates' in result and result['candidates'] and 'content' in result['candidates'][0] and 'parts' in result['candidates'][0]['content']:
                    for part in result['candidates'][0]['content']['parts']:
                        if 'inlineData' in part:
                            image_data_b64 = part['inlineData']['data']
                            import base64
                            
                            # 성공 로깅
                            image_bytes = base64.b64decode(image_data_b64)
                            self._log_request('generateContent', True, len(image_bytes), usage_metadata)
                            
                            print("[이미지 생성 API] ✅ 이미지 데이터 수신 및 디코딩 성공")
                            return image_bytes
                
                # 이미지가 생성되지 않은 이유 확인 (안전 필터 등)
                if 'candidates' in result and result['candidates']:
                    finish_reason = result['candidates'][0].get('finishReason')
                    if finish_reason == 'NO_IMAGE':
                        print("[이미지 생성 API] ❌ 모델이 이미지를 생성하지 않았습니다. (이유: NO_IMAGE)")
                        st.error("❌ 모델이 이미지를 생성하지 않았습니다. (이유: NO_IMAGE)")
                        st.info("💡 프롬프트가 안전 정책에 위배되거나 모호할 수 있습니다. 등장인물 설명을 수정해 보세요.")
                    elif finish_reason == 'SAFETY':
                        print("[이미지 생성 API] ❌ 안전 필터에 의해 이미지 생성이 차단되었습니다.")
                        st.error("❌ 안전 필터에 의해 이미지 생성이 차단되었습니다.")

                # 실패 로깅
                print("[이미지 생성 API] ❌ API 응답에 이미지 데이터가 없습니다.")
                self._log_request('generateContent', False, len(response.text), usage_metadata)
                st.error("API 응답에 이미지 데이터가 없습니다.")
                st.json(result)
                return None
            else:
                # 실패 로깅
                self._log_request('generateContent', False, len(response.text))
                print(f"[이미지 생성 API] ❌ API 오류: {response.status_code} - {response.text}")
                st.error(f"제미나이 이미지 API 오류: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("[이미지 생성 API] ❌ 요청 타임아웃")
            st.error("❌ 이미지 생성 요청이 타임아웃되었습니다. 잠시 후 다시 시도해주세요.")
            return None
        except requests.exceptions.ConnectionError:
            print("[이미지 생성 API] ❌ 네트워크 연결 오류")
            st.error("❌ 네트워크 연결 오류로 이미지 생성에 실패했습니다.")
            return None
        except Exception as e:
            import traceback
            print(f"[이미지 생성 API] ❌ 예외 발생: {str(e)}")
            print(traceback.format_exc())
            st.code(traceback.format_exc())
            st.error(f"제미나이 이미지 API 요청 실패: {str(e)}")
            return None