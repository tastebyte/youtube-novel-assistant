"""
보안 관련 유틸리티
"""

import os
import hashlib
import secrets
from typing import Optional
import streamlit as st


def mask_api_key(api_key: str) -> str:
    """API 키를 마스킹하여 표시"""
    if not api_key:
        return "설정되지 않음"
    
    if len(api_key) <= 8:
        return "*" * len(api_key)
    
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]


def validate_api_key_format(api_key: str, service: str) -> bool:
    """API 키 형식 검증"""
    if not api_key:
        return False
    
    if service.lower() == 'gemini':
        # Gemini API 키는 보통 39자리
        return len(api_key) >= 30 and api_key.startswith('AI')
    
    return len(api_key) >= 20  # 기본 최소 길이


def get_secure_api_key(service: str) -> Optional[str]:
    """보안을 고려한 API 키 조회"""
    # 1. Streamlit secrets에서 먼저 확인
    try:
        if hasattr(st, 'secrets') and service.upper() + '_API_KEY' in st.secrets:
            return st.secrets[service.upper() + '_API_KEY']
    except:
        pass
    
    # 2. 환경 변수에서 확인
    env_key = f"{service.upper()}_API_KEY"
    api_key = os.getenv(env_key)
    
    if api_key and validate_api_key_format(api_key, service):
        return api_key
    
    return None


def log_api_usage(service: str, endpoint: str, success: bool, response_size: int = 0):
    """API 사용량 로깅 (보안 감사용)"""
    try:
        # 민감한 정보는 제외하고 로깅
        log_entry = {
            'service': service,
            'endpoint': endpoint,
            'success': success,
            'response_size': response_size,
            'timestamp': st.session_state.get('current_time', 'unknown')
        }
        
        # 개발 환경에서만 로깅
        if os.getenv('ENVIRONMENT') == 'development':
            st.write(f"API 사용: {log_entry}")
            
    except Exception:
        # 로깅 실패는 무시 (메인 기능에 영향 없도록)
        pass


def sanitize_filename(filename: str) -> str:
    """파일명 보안 처리"""
    # 위험한 문자 제거
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '..']
    
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # 길이 제한
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename


def generate_secure_id() -> str:
    """보안을 고려한 고유 ID 생성"""
    return secrets.token_urlsafe(16)


def hash_sensitive_data(data: str) -> str:
    """민감한 데이터 해싱"""
    return hashlib.sha256(data.encode()).hexdigest()


class SecureAPIClient:
    """보안 강화된 API 클라이언트 기본 클래스"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.api_key = get_secure_api_key(service_name)
        self.request_count = 0
        self.max_requests_per_minute = 60  # 기본 제한
    
    def _check_rate_limit(self) -> bool:
        """요청 빈도 제한 확인 (더 엄격하게)"""
        import time
        
        current_time = time.time()
        last_request_time = st.session_state.get(f'last_request_{self.service_name}', 0)
        
        # 3초 간격 강제 (더 안전하게)
        time_diff = current_time - last_request_time
        if time_diff < 3:
            remaining_time = 3 - time_diff
            st.warning(f"⏳ {self.service_name} API 요청 제한: {remaining_time:.1f}초 후 다시 시도해주세요.")
            return False
        
        st.session_state[f'last_request_{self.service_name}'] = current_time
        return True
    
    def _log_request(self, endpoint: str, success: bool, response_size: int = 0):
        """요청 로깅"""
        self.request_count += 1
        log_api_usage(self.service_name, endpoint, success, response_size)
    
    def get_masked_key(self) -> str:
        """마스킹된 API 키 반환"""
        return mask_api_key(self.api_key or "")


def check_security_settings():
    """보안 설정 확인"""
    issues = []
    
    # API 키 확인
    gemini_key = get_secure_api_key('gemini')
    if not gemini_key:
        issues.append("Gemini API 키가 설정되지 않았습니다.")
    elif not validate_api_key_format(gemini_key, 'gemini'):
        issues.append("Gemini API 키 형식이 올바르지 않습니다.")
    
    # 환경 변수 확인
    if os.getenv('ENVIRONMENT') == 'production':
        if not os.getenv('SECRET_KEY'):
            issues.append("프로덕션 환경에서 SECRET_KEY가 설정되지 않았습니다.")
    
    return issues