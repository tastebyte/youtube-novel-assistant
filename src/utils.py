"""
유틸리티 함수 모음
"""

import os
from pathlib import Path
import streamlit as st


def get_api_key(service: str) -> str:
    """Streamlit secrets 또는 환경 변수에서 API 키를 가져옵니다."""
    key_name = f"{service.upper()}_API_KEY"
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, "")


def get_data_directory() -> Path:
    """데이터 디렉토리 경로를 반환하고, 없으면 생성합니다."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_novel_directory(novel_id: str) -> Path:
    """소설별 디렉토리 경로를 반환하고, 없으면 생성합니다."""
    novel_dir = get_data_directory() / "novels" / novel_id
    novel_dir.mkdir(parents=True, exist_ok=True)
    return novel_dir


def get_images_directory(novel_id: str) -> Path:
    """이미지 디렉토리 경로를 반환하고, 없으면 생성합니다."""
    images_dir = get_novel_directory(novel_id) / "images"
    (images_dir / "characters").mkdir(parents=True, exist_ok=True)
    (images_dir / "scenes").mkdir(parents=True, exist_ok=True)
    return images_dir


def get_backups_directory() -> Path:
    """백업 디렉토리 경로를 반환하고, 없으면 생성합니다."""
    backup_dir = get_data_directory() / "backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def ensure_directory(path: Path):
    """디렉토리가 없으면 생성합니다."""
    path.mkdir(parents=True, exist_ok=True)