# BharatVaani/core/error_handler.py

"""
Centralized error handling and validation for BharatVaani
"""

import logging
from functools import wraps
from flask import jsonify, flash, redirect, url_for, request
from typing import Callable, Any


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class APIError(Exception):
    """Custom exception for API-related errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def validate_article_id(article_id: str) -> bool:
    """Validate article ID format - relaxed validation"""
    if not article_id or not isinstance(article_id, str):
        return False
    # More lenient: just check it's not empty and not too long
    if len(article_id) < 1 or len(article_id) > 200:
        return False
    return True


def validate_language_code(lang_code: str, supported_languages: dict) -> bool:
    """Validate language code against supported languages"""
    return lang_code in supported_languages or lang_code == 'en'


def validate_text_length(text: str, min_length: int = 1, max_length: int = 5000) -> bool:
    """Validate text length"""
    if not text or not isinstance(text, str):
        return False
    text_len = len(text.strip())
    return min_length <= text_len <= max_length


def handle_api_errors(f: Callable) -> Callable:
    """
    Decorator to handle API endpoint errors gracefully.
    Returns JSON error responses for API routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logging.warning(f"Validation error in {f.__name__}: {e.message}")
            return jsonify({
                'success': False,
                'error': e.message,
                'field': e.field
            }), 400
        except APIError as e:
            logging.error(f"API error in {f.__name__}: {e.message}")
            return jsonify({
                'success': False,
                'error': e.message
            }), e.status_code
        except Exception as e:
            logging.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred. Please try again.'
            }), 500
    return decorated_function


def handle_page_errors(f: Callable) -> Callable:
    """
    Decorator to handle page route errors gracefully.
    Redirects to appropriate pages with flash messages.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            flash(f'An error occurred: {str(e)}', 'error')
            # Redirect to dashboard or previous page
            return redirect(request.referrer or url_for('dashboard'))
    return decorated_function


def safe_get_from_dict(dictionary: dict, key: str, default: Any = None, expected_type: type = None) -> Any:
    """
    Safely get value from dictionary with optional type checking.
    
    Args:
        dictionary: Source dictionary
        key: Key to retrieve
        default: Default value if key not found
        expected_type: Expected type of the value (optional)
    
    Returns:
        Value from dictionary or default
    """
    try:
        value = dictionary.get(key, default)
        
        if expected_type and value is not None:
            if not isinstance(value, expected_type):
                logging.warning(f"Type mismatch for key '{key}': expected {expected_type}, got {type(value)}")
                return default
        
        return value
    except Exception as e:
        logging.error(f"Error getting key '{key}' from dict: {e}")
        return default


def sanitize_input(text: str, max_length: int = 5000) -> str:
    """
    Sanitize user input by removing potentially harmful characters.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove any null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


class RateLimiter:
    """
    Simple in-memory rate limiter for API endpoints.
    """
    def __init__(self):
        self.requests = {}
        self.limits = {
            'default': (60, 60),  # 60 requests per 60 seconds
            'translate': (30, 60),  # 30 requests per 60 seconds
            'audio': (20, 60),  # 20 requests per 60 seconds
            'simplify': (10, 60),  # 10 requests per 60 seconds
            'what_if': (5, 300),  # 5 requests per 5 minutes
        }
    
    def is_allowed(self, user_id: str, endpoint: str = 'default') -> tuple[bool, str]:
        """
        Check if request is allowed based on rate limits.
        
        Returns:
            (is_allowed: bool, message: str)
        """
        import time
        
        limit, window = self.limits.get(endpoint, self.limits['default'])
        key = f"{user_id}:{endpoint}"
        current_time = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the time window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < window
        ]
        
        if len(self.requests[key]) >= limit:
            return False, f"Rate limit exceeded. Try again in {int(window - (current_time - self.requests[key][0]))} seconds."
        
        self.requests[key].append(current_time)
        return True, ""


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
