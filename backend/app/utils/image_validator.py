"""
Image validation utilities for Google Ads campaigns.

This module validates image dimensions and aspect ratios for campaign assets.
"""
import logging
import requests
from io import BytesIO
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Image requirements for different asset types
IMAGE_REQUIREMENTS = {
    'landscape': {
        'ratio': 1.91,
        'ratio_tolerance': 0.02,
        'min_width': 600,
        'min_height': 314,
        'max_file_size': 5 * 1024 * 1024,  # 5MB
        'description': 'Landscape marketing image (1.91:1)',
    },
    'square': {
        'ratio': 1.0,
        'ratio_tolerance': 0.02,
        'min_width': 300,
        'min_height': 300,
        'max_file_size': 5 * 1024 * 1024,
        'description': 'Square marketing image (1:1)',
    },
    'logo': {
        'ratio': 1.0,
        'ratio_tolerance': 0.02,
        'min_width': 128,
        'min_height': 128,
        'max_file_size': 5 * 1024 * 1024,
        'description': 'Square logo (1:1)',
    },
    'logo_landscape': {
        'ratio': 4.0,
        'ratio_tolerance': 0.1,  # More tolerance for 4:1 ratio
        'min_width': 512,
        'min_height': 128,
        'max_file_size': 5 * 1024 * 1024,
        'description': 'Landscape logo (4:1)',
    },
}

# Supported image formats
SUPPORTED_FORMATS = ['JPEG', 'PNG', 'GIF', 'WEBP']
SUPPORTED_MIME_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
]


def validate_aspect_ratio(
    width: int,
    height: int,
    expected_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate that image dimensions match the expected aspect ratio.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        expected_type: Expected image type (landscape, square, logo, logo_landscape)

    Returns:
        Tuple of (is_valid, error_message)
    """
    requirements = IMAGE_REQUIREMENTS.get(expected_type)
    if not requirements:
        return False, f"Unknown image type: {expected_type}"

    if width <= 0 or height <= 0:
        return False, "Invalid image dimensions"

    # Calculate actual ratio
    actual_ratio = width / height
    expected_ratio = requirements['ratio']
    tolerance = requirements['ratio_tolerance']

    # Check if ratio is within tolerance
    ratio_diff = abs(actual_ratio - expected_ratio) / expected_ratio
    if ratio_diff > tolerance:
        return False, (
            f"Image aspect ratio {actual_ratio:.2f} does not match required ratio "
            f"{expected_ratio:.2f} (tolerance: {tolerance * 100:.0f}%)"
        )

    return True, None


def validate_image_dimensions(
    width: int,
    height: int,
    expected_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate that image dimensions meet minimum requirements.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        expected_type: Expected image type (landscape, square, logo, logo_landscape)

    Returns:
        Tuple of (is_valid, error_message)
    """
    requirements = IMAGE_REQUIREMENTS.get(expected_type)
    if not requirements:
        return False, f"Unknown image type: {expected_type}"

    min_width = requirements['min_width']
    min_height = requirements['min_height']

    if width < min_width:
        return False, (
            f"Image width {width}px is below minimum required {min_width}px "
            f"for {requirements['description']}"
        )

    if height < min_height:
        return False, (
            f"Image height {height}px is below minimum required {min_height}px "
            f"for {requirements['description']}"
        )

    return True, None


def get_image_dimensions_from_bytes(image_bytes: bytes) -> Optional[Dict[str, int]]:
    """
    Get image dimensions from raw bytes without PIL.

    This is a lightweight fallback when PIL is not available.
    Supports JPEG, PNG, and GIF.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Dictionary with width and height, or None if unable to determine
    """
    if len(image_bytes) < 24:
        return None

    # PNG: Check for PNG signature and read IHDR chunk
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        if image_bytes[12:16] == b'IHDR':
            width = int.from_bytes(image_bytes[16:20], 'big')
            height = int.from_bytes(image_bytes[20:24], 'big')
            return {'width': width, 'height': height}

    # JPEG: Parse markers to find SOF (Start Of Frame)
    if image_bytes[:2] == b'\xff\xd8':
        offset = 2
        while offset < len(image_bytes) - 9:
            marker = image_bytes[offset:offset + 2]
            if marker[0] != 0xff:
                break
            if marker[1] == 0xd9:  # End of image
                break
            if marker[1] in (0xc0, 0xc1, 0xc2):  # SOF markers
                height = int.from_bytes(image_bytes[offset + 5:offset + 7], 'big')
                width = int.from_bytes(image_bytes[offset + 7:offset + 9], 'big')
                return {'width': width, 'height': height}
            # Move to next marker
            if offset + 4 > len(image_bytes):
                break
            length = int.from_bytes(image_bytes[offset + 2:offset + 4], 'big')
            offset += 2 + length

    # GIF: Read logical screen descriptor
    if image_bytes[:6] in (b'GIF87a', b'GIF89a'):
        width = int.from_bytes(image_bytes[6:8], 'little')
        height = int.from_bytes(image_bytes[8:10], 'little')
        return {'width': width, 'height': height}

    return None


def validate_image_from_url(url: str, expected_type: str) -> Dict[str, Any]:
    """
    Download and validate an image from URL.

    Args:
        url: URL of the image to validate
        expected_type: Expected image type (landscape, square, logo)

    Returns:
        Dictionary with:
        - valid: bool
        - errors: list of error messages
        - dimensions: dict with width and height (if available)
        - file_size: int (if available)
    """
    result = {
        'valid': False,
        'errors': [],
        'dimensions': None,
        'file_size': None,
    }

    if not url:
        result['errors'].append('Image URL is required')
        return result

    requirements = IMAGE_REQUIREMENTS.get(expected_type)
    if not requirements:
        result['errors'].append(f'Unknown image type: {expected_type}')
        return result

    try:
        # Download image with timeout
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if not any(mime in content_type for mime in SUPPORTED_MIME_TYPES):
            result['errors'].append(
                f'Unsupported image format. Supported: JPEG, PNG, GIF, WEBP'
            )
            return result

        # Get content length if available
        content_length = response.headers.get('content-length')
        if content_length:
            file_size = int(content_length)
            result['file_size'] = file_size

            max_size = requirements.get('max_file_size', 5 * 1024 * 1024)
            if file_size > max_size:
                result['errors'].append(
                    f'Image file size ({file_size / 1024 / 1024:.1f}MB) '
                    f'exceeds maximum ({max_size / 1024 / 1024:.1f}MB)'
                )
                return result

        # Read image content
        image_bytes = response.content
        result['file_size'] = len(image_bytes)

        # Try to get dimensions using PIL if available
        try:
            from PIL import Image
            image = Image.open(BytesIO(image_bytes))
            width, height = image.size
        except ImportError:
            # Fall back to manual parsing
            dims = get_image_dimensions_from_bytes(image_bytes)
            if dims:
                width, height = dims['width'], dims['height']
            else:
                result['errors'].append('Unable to determine image dimensions')
                return result

        result['dimensions'] = {'width': width, 'height': height}

        # Validate dimensions
        valid_dims, error = validate_image_dimensions(width, height, expected_type)
        if not valid_dims:
            result['errors'].append(error)

        # Validate aspect ratio
        valid_ratio, error = validate_aspect_ratio(width, height, expected_type)
        if not valid_ratio:
            result['errors'].append(error)

        # Set valid flag
        result['valid'] = len(result['errors']) == 0

    except requests.exceptions.Timeout:
        result['errors'].append('Image download timed out')
    except requests.exceptions.RequestException as e:
        result['errors'].append(f'Failed to download image: {str(e)}')
    except Exception as e:
        logger.error(f'Error validating image from {url}: {e}')
        result['errors'].append(f'Failed to validate image: {str(e)}')

    return result


def validate_campaign_images(images: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """
    Validate all images for a campaign.

    Args:
        images: Dictionary with image URLs (landscape_url, square_url, logo_url)

    Returns:
        Dictionary with validation results for each image type
    """
    results = {
        'valid': True,
        'errors': [],
        'details': {},
    }

    if not images:
        return results

    type_mapping = {
        'landscape_url': 'landscape',
        'square_url': 'square',
        'logo_url': 'logo',
    }

    for url_key, image_type in type_mapping.items():
        url = images.get(url_key)
        if url:
            validation = validate_image_from_url(url, image_type)
            results['details'][url_key] = validation

            if not validation['valid']:
                results['valid'] = False
                for error in validation['errors']:
                    results['errors'].append(f"{image_type.title()}: {error}")

    return results


def get_image_requirements(expected_type: str) -> Optional[Dict[str, Any]]:
    """
    Get the requirements for a specific image type.

    Args:
        expected_type: Image type (landscape, square, logo, logo_landscape)

    Returns:
        Dictionary with requirements or None if type not found
    """
    return IMAGE_REQUIREMENTS.get(expected_type)


def suggest_image_type(width: int, height: int) -> Optional[str]:
    """
    Suggest the best image type based on dimensions.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Suggested image type or None if no match
    """
    if width <= 0 or height <= 0:
        return None

    ratio = width / height

    best_match = None
    best_diff = float('inf')

    for image_type, requirements in IMAGE_REQUIREMENTS.items():
        expected_ratio = requirements['ratio']
        tolerance = requirements['ratio_tolerance']
        ratio_diff = abs(ratio - expected_ratio) / expected_ratio

        if ratio_diff <= tolerance and ratio_diff < best_diff:
            # Also check minimum dimensions
            if width >= requirements['min_width'] and height >= requirements['min_height']:
                best_match = image_type
                best_diff = ratio_diff

    return best_match
