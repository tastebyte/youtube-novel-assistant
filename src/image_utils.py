"""
이미지 처리 유틸리티
"""

import io
import base64
from PIL import Image
import streamlit as st
from typing import Optional, Tuple


def compress_image(image_data: bytes, quality: int = 85, max_width: int = 800) -> Optional[bytes]:
    """
    이미지 압축 (참고 로직의 compressImage 함수와 동일한 기능)
    
    Args:
        image_data: 원본 이미지 데이터 (bytes)
        quality: JPEG 품질 (1-100, 기본값 85)
        max_width: 최대 너비 (기본값 800px)
    
    Returns:
        압축된 이미지 데이터 (bytes) 또는 None
    """
    try:
        # PIL Image로 변환
        image = Image.open(io.BytesIO(image_data))
        
        # RGBA를 RGB로 변환 (JPEG는 투명도 지원 안함)
        if image.mode in ('RGBA', 'LA', 'P'):
            # 흰색 배경으로 변환
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 크기 조정 (참고 로직과 동일한 비율 유지)
        width, height = image.size
        if width > max_width:
            height = int((max_width / width) * height)
            width = max_width
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # JPEG로 압축
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_data = output.getvalue()
        
        # 압축률 계산 및 로그
        original_size = len(image_data)
        compressed_size = len(compressed_data)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        st.info(f"이미지 압축 완료: {original_size:,} bytes → {compressed_size:,} bytes ({compression_ratio:.1f}% 감소)")
        
        return compressed_data
        
    except Exception as e:
        st.error(f"이미지 압축 실패: {str(e)}")
        return image_data  # 압축 실패 시 원본 반환


def base64_to_bytes(base64_string: str) -> Optional[bytes]:
    """
    Base64 문자열을 bytes로 변환
    
    Args:
        base64_string: data:image/... 형태의 base64 문자열
    
    Returns:
        이미지 데이터 (bytes) 또는 None
    """
    try:
        if base64_string.startswith('data:image'):
            # data:image/png;base64, 부분 제거
            base64_data = base64_string.split(',')[1]
        else:
            base64_data = base64_string
        
        return base64.b64decode(base64_data)
        
    except Exception as e:
        st.error(f"Base64 디코딩 실패: {str(e)}")
        return None


def bytes_to_base64(image_data: bytes, mime_type: str = "image/jpeg") -> str:
    """
    bytes를 Base64 문자열로 변환
    
    Args:
        image_data: 이미지 데이터 (bytes)
        mime_type: MIME 타입 (기본값: image/jpeg)
    
    Returns:
        data:image/... 형태의 base64 문자열
    """
    try:
        base64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}"
        
    except Exception as e:
        st.error(f"Base64 인코딩 실패: {str(e)}")
        return ""


def get_image_info(image_data: bytes) -> dict:
    """
    이미지 정보 반환
    
    Args:
        image_data: 이미지 데이터 (bytes)
    
    Returns:
        이미지 정보 딕셔너리
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        
        return {
            'size': image.size,
            'width': image.width,
            'height': image.height,
            'mode': image.mode,
            'format': image.format,
            'file_size': len(image_data)
        }
        
    except Exception as e:
        st.error(f"이미지 정보 조회 실패: {str(e)}")
        return {}


def resize_image(image_data: bytes, target_size: Tuple[int, int], maintain_aspect: bool = True) -> Optional[bytes]:
    """
    이미지 크기 조정
    
    Args:
        image_data: 원본 이미지 데이터 (bytes)
        target_size: 목표 크기 (width, height)
        maintain_aspect: 비율 유지 여부
    
    Returns:
        크기 조정된 이미지 데이터 (bytes) 또는 None
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        
        if maintain_aspect:
            # 비율 유지하면서 크기 조정
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
        else:
            # 정확한 크기로 조정
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # RGB 변환 (필요한 경우)
        if image.mode != 'RGB':
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            else:
                image = image.convert('RGB')
        
        # JPEG로 저장
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        
        return output.getvalue()
        
    except Exception as e:
        st.error(f"이미지 크기 조정 실패: {str(e)}")
        return None


def create_thumbnail(image_data: bytes, size: int = 200) -> Optional[bytes]:
    """
    썸네일 이미지 생성
    
    Args:
        image_data: 원본 이미지 데이터 (bytes)
        size: 썸네일 크기 (정사각형, 기본값 200px)
    
    Returns:
        썸네일 이미지 데이터 (bytes) 또는 None
    """
    return resize_image(image_data, (size, size), maintain_aspect=True)


def optimize_for_web(image_data: bytes) -> Optional[bytes]:
    """
    웹 최적화 (참고 로직의 압축 설정과 동일)
    
    Args:
        image_data: 원본 이미지 데이터 (bytes)
    
    Returns:
        웹 최적화된 이미지 데이터 (bytes) 또는 None
    """
    # 참고 로직과 동일한 설정: quality=0.7, maxWidth=800
    return compress_image(image_data, quality=70, max_width=800)