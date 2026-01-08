"""
ImageKit Utilities
Functions for generating authentication parameters and managing images in ImageKit.
"""

import time
import uuid
import hmac
import hashlib
from typing import Optional

from imagekitio import ImageKit

from src.config.settings import settings
from src.config.logger import logger


def get_imagekit_client() -> ImageKit:
    """Get configured ImageKit client."""
    if not settings.IMAGEKIT_PRIVATE_KEY:
        raise ValueError("ImageKit credentials not configured. Please set IMAGEKIT_PRIVATE_KEY in .env file")
    
    return ImageKit(
        private_key=settings.IMAGEKIT_PRIVATE_KEY
    )


def generate_auth_params(folder: str = "/users", token: Optional[str] = None, expire: Optional[int] = None) -> dict:
    """
    Generate authentication parameters for client-side ImageKit uploads.
    
    Args:
        folder: Folder path to upload to (default: "/users")
        token: Optional custom token (defaults to UUID)
        expire: Optional expiry time in seconds from now (defaults to 600 seconds / 10 minutes)
        
    Returns:
        Dictionary with 'token', 'expire', 'signature', and 'folder' for client-side authentication
        
    Example response:
        {
            "token": "<uuid-token>",
            "expire": <unix-timestamp>,
            "signature": "<hmac-signature>",
            "folder": "/users"
        }
    """
    if not settings.IMAGEKIT_PRIVATE_KEY:
        raise ValueError("ImageKit credentials not configured")
    
    # Generate token if not provided
    auth_token = token or str(uuid.uuid4())
    
    # Calculate expiry timestamp (default 10 minutes from now)
    expire_time = expire if expire else int(time.time()) + 600
    
    # Generate HMAC-SHA1 signature
    message = f"{auth_token}{expire_time}"
    signature = hmac.new(
        settings.IMAGEKIT_PRIVATE_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha1
    ).hexdigest()
    
    logger.info("Generated ImageKit auth params with token: %s, folder: %s", auth_token[:8] + "...", folder)
    
    return {
        "token": auth_token,
        "expire": expire_time,
        "signature": signature,
        "folder": folder
    }


def delete_image(file_id: str) -> bool:
    """
    Delete an image from ImageKit.
    
    Args:
        file_id: The ImageKit file ID
        
    Returns:
        True if deleted successfully, False otherwise
    """
    if not file_id:
        return False
        
    try:
        client = get_imagekit_client()
        client.delete_file(file_id)
        
        logger.info("Deleted ImageKit image: %s", file_id)
        return True
        
    except Exception as e:
        logger.error("Error deleting ImageKit image %s: %s", file_id, str(e))
        return False


def get_image_url(file_id: str, path: str) -> str:
    """
    Get the public URL for an ImageKit image.
    
    Args:
        file_id: The ImageKit file ID
        path: The file path in ImageKit
        
    Returns:
        Full ImageKit URL
        
    Note:
        The actual URL structure depends on your ImageKit URL endpoint.
        Client should store and use the URL returned from upload response.
    """
    # ImageKit URLs are typically provided in the upload response
    # This is a fallback for generating URLs if needed
    return path
