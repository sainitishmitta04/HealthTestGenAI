import os
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_unique_id(prefix: str = "TC") -> str:
    """
    Generate a unique ID with timestamp and random component
    
    Args:
        prefix (str): Prefix for the ID
        
    Returns:
        str: Unique ID
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_component = hashlib.md5(os.urandom(4)).hexdigest()[:6]
    return f"{prefix}-{timestamp}-{random_component}"

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid email format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted file size
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.2f} {size_names[i]}"

def safe_json_parse(json_string: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with error handling
    
    Args:
        json_string (str): JSON string to parse
        default (Any): Default value if parsing fails
        
    Returns:
        Any: Parsed JSON object or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dump(data: Any, indent: Optional[int] = None) -> str:
    """
    Safely convert data to JSON string with error handling
    
    Args:
        data (Any): Data to convert to JSON
        indent (int, optional): Indentation level
        
    Returns:
        str: JSON string or empty string on error
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return ""

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters for Windows/Linux filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip().strip('.')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    return filename

def create_directory(path: str) -> bool:
    """
    Create directory if it doesn't exist
    
    Args:
        path (str): Directory path
        
    Returns:
        bool: True if directory created or exists
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def get_file_extension(filename: str) -> str:
    """
    Get file extension in lowercase
    
    Args:
        filename (str): Filename
        
    Returns:
        str: File extension (including dot) or empty string
    """
    return Path(filename).suffix.lower()

def is_supported_file_format(filename: str, supported_formats: List[str]) -> bool:
    """
    Check if file format is supported
    
    Args:
        filename (str): Filename to check
        supported_formats (List[str]): List of supported formats
        
    Returns:
        bool: True if format is supported
    """
    file_ext = get_file_extension(filename)
    return file_ext in supported_formats

def format_timestamp(timestamp: Optional[datetime] = None, 
                    format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp to string
    
    Args:
        timestamp (datetime, optional): Timestamp to format (default: current time)
        format_str (str): Format string
        
    Returns:
        str: Formatted timestamp
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime(format_str)

def parse_timestamp(timestamp_str: str, 
                  format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse timestamp string to datetime object
    
    Args:
        timestamp_str (str): Timestamp string
        format_str (str): Format string
        
    Returns:
        Optional[datetime]: Datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(timestamp_str, format_str)
    except (ValueError, TypeError):
        return None

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size
    
    Args:
        lst (List[Any]): List to chunk
        chunk_size (int): Size of each chunk
        
    Returns:
        List[List[Any]]: List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def flatten_list(nested_list: List[Any]) -> List[Any]:
    """
    Flatten a nested list
    
    Args:
        nested_list (List[Any]): Nested list to flatten
        
    Returns:
        List[Any]: Flattened list
    """
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries
    
    Args:
        dict1 (Dict[str, Any]): First dictionary
        dict2 (Dict[str, Any]): Second dictionary
        
    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if (key in result and isinstance(result[key], dict) and 
            isinstance(value, dict)):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from dictionary
    
    Args:
        data (Dict[str, Any]): Dictionary to clean
        
    Returns:
        Dict[str, Any]: Cleaned dictionary
    """
    return {k: v for k, v in data.items() if v is not None}

def get_environment_variable(key: str, default: Any = None) -> Any:
    """
    Get environment variable with type conversion
    
    Args:
        key (str): Environment variable name
        default (Any): Default value if not found
        
    Returns:
        Any: Environment variable value
    """
    value = os.getenv(key)
    if value is None:
        return default
    
    # Try to convert to appropriate type
    try:
        # Boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        # Integer
        elif value.isdigit():
            return int(value)
        # Float
        elif value.replace('.', '', 1).isdigit():
            return float(value)
        # JSON
        elif value.startswith('{') or value.startswith('['):
            return json.loads(value)
        # String
        else:
            return value
    except (ValueError, json.JSONDecodeError):
        return value

def calculate_md5_hash(data: str) -> str:
    """
    Calculate MD5 hash of string data
    
    Args:
        data (str): Data to hash
        
    Returns:
        str: MD5 hash
    """
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def calculate_file_hash(file_path: str) -> Optional[str]:
    """
    Calculate MD5 hash of file content
    
    Args:
        file_path (str): Path to file
        
    Returns:
        Optional[str]: MD5 hash or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate file hash for {file_path}: {e}")
        return None

def retry_operation(operation, max_attempts: int = 3, delay: float = 1.0, 
                   exceptions: tuple = (Exception,)):
    """
    Retry decorator for operations that might fail
    
    Args:
        operation: Function to retry
        max_attempts (int): Maximum number of attempts
        delay (float): Delay between attempts in seconds
        exceptions (tuple): Exceptions to catch and retry on
        
    Returns:
        Any: Result of the operation
    """
    import time
    
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(max_attempts):
            try:
                return operation(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise last_exception
        raise last_exception
    
    return wrapper

def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format
    
    Args:
        seconds (float): Duration in seconds
        
    Returns:
        str: Formatted duration
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:.0f}m {seconds:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"

def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid URL format
    """
    import re
    pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))

def truncate_text(text: str, max_length: int, ellipsis: str = "...") -> str:
    """
    Truncate text to maximum length with ellipsis
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        ellipsis (str): Ellipsis string
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(ellipsis)] + ellipsis


# if __name__ == "__main__":
#     # Example usage
#     print("Unique ID:", generate_unique_id())
#     print("Formatted size:", format_file_size(1024 * 1024))
#     print("Sanitized filename:", sanitize_filename('file<name>.txt'))
#     print("Formatted timestamp:", format_timestamp())