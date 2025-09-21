import os
import json
import logging
from typing import Dict, List,Any, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigManager:
    """Manage application configuration and settings"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration manager
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config_file = config_file
        self.config = self._load_default_config()
        self._ensure_config_directory()
    
    def _ensure_config_directory(self) -> None:
        """Ensure the configuration directory exists"""
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "app": {
                "name": "Healthcare TestGen AI",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "database": {
                "path": "data/testgen.db",
                "auto_backup": True,
                "backup_interval": 24  # hours
            },
            "ai": {
                "model_temperature": 0.7,
                "max_tokens": 1000,
                "timeout": 30  # seconds
            },
            "file_processing": {
                "max_file_size_mb": 10,
                "supported_formats": [".pdf", ".docx", ".xml", ".json", ".md", ".txt"]
            },
            "integrations": {
                "jira": {
                    "enabled": False,
                    "base_url": "",
                    "project_key": ""
                },
                "polarion": {
                    "enabled": False,
                    "base_url": "",
                    "project_id": ""
                },
                "azure_devops": {
                    "enabled": False,
                    "organization_url": "",
                    "project_name": ""
                }
            },
            "compliance": {
                "enabled_standards": ["FDA", "ISO 13485"],
                "auto_check": True
            },
            "export": {
                "default_format": "json",
                "include_timestamps": True,
                "backup_exports": True
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Returns:
            Dict[str, Any]: Configuration data
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with default config (deep merge)
                    self._deep_merge(self.config, loaded_config)
                    logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.warning(f"Config file {self.config_file} not found, using defaults")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
        
        return self.config
    
    def save_config(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to file
        
        Args:
            config_data (Dict[str, Any], optional): Configuration data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if config_data:
                self._deep_merge(self.config, config_data)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key
        
        Args:
            key (str): Configuration key (dot notation supported)
            default (Any): Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value
        
        Args:
            key (str): Configuration key (dot notation supported)
            value (Any): Value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            keys = key.split('.')
            config_ptr = self.config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config_ptr:
                    config_ptr[k] = {}
                config_ptr = config_ptr[k]
            
            # Set the value
            config_ptr[keys[-1]] = value
            return True
        except Exception as e:
            logger.error(f"Error setting configuration key {key}: {e}")
            return False
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        Deep merge two dictionaries
        
        Args:
            base (Dict[str, Any]): Base dictionary to merge into
            update (Dict[str, Any]): Dictionary with updates
        """
        for key, value in update.items():
            if (key in base and isinstance(base[key], dict) and 
                isinstance(value, dict)):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def validate_config(self) -> Dict[str, List[str]]:
        """
        Validate configuration values
        
        Returns:
            Dict[str, List[str]]: Validation errors by category
        """
        errors = {}
        
        # Validate database path
        db_path = self.get('database.path')
        if db_path:
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except Exception as e:
                    errors.setdefault('database', []).append(f"Cannot create database directory: {e}")
        
        # Validate file size limit
        max_size = self.get('file_processing.max_file_size_mb')
        if not isinstance(max_size, (int, float)) or max_size <= 0:
            errors.setdefault('file_processing', []).append("Max file size must be a positive number")
        
        # Validate AI settings
        temperature = self.get('ai.model_temperature')
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1:
            errors.setdefault('ai', []).append("Model temperature must be between 0 and 1")
        
        max_tokens = self.get('ai.max_tokens')
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            errors.setdefault('ai', []).append("Max tokens must be a positive integer")
        
        return errors
    
    def get_environment_config(self) -> Dict[str, Any]:
        """
        Get environment-specific configuration
        
        Returns:
            Dict[str, Any]: Environment configuration
        """
        env = os.getenv('APP_ENV', 'development').lower()
        
        env_config = {
            'development': {
                'app': {'debug': True, 'log_level': 'DEBUG'},
                'database': {'path': 'data/testgen_dev.db'}
            },
            'testing': {
                'app': {'debug': False, 'log_level': 'INFO'},
                'database': {'path': 'data/testgen_test.db'}
            },
            'production': {
                'app': {'debug': False, 'log_level': 'WARNING'},
                'database': {'path': 'data/testgen_prod.db'}
            }
        }
        
        return env_config.get(env, {})


# Global configuration instance
_config_instance = None

def get_config(config_file: str = "config.json") -> ConfigManager:
    """
    Get or create global configuration instance
    
    Args:
        config_file (str): Path to configuration file
        
    Returns:
        ConfigManager: Configuration manager instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_file)
        _config_instance.load_config()
    return _config_instance

def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from file
    
    Args:
        config_file (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration data
    """
    return get_config(config_file).load_config()

def save_config(config_data: Dict[str, Any], config_file: str = "config.json") -> bool:
    """
    Save configuration to file
    
    Args:
        config_data (Dict[str, Any]): Configuration data to save
        config_file (str): Path to configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    return get_config(config_file).save_config(config_data)

def get_config_value(key: str, default: Any = None, config_file: str = "config.json") -> Any:
    """
    Get configuration value by key
    
    Args:
        key (str): Configuration key
        default (Any): Default value if key not found
        config_file (str): Path to configuration file
        
    Returns:
        Any: Configuration value
    """
    return get_config(config_file).get(key, default)

def set_config_value(key: str, value: Any, config_file: str = "config.json") -> bool:
    """
    Set configuration value
    
    Args:
        key (str): Configuration key
        value (Any): Value to set
        config_file (str): Path to configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    return get_config(config_file).set(key, value)

