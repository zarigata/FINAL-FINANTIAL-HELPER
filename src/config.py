#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# CONFIGURATION MANAGER v1.0
# CODEX: This module handles loading, validating, and providing access to configuration settings.
# CODEX: It ensures all components have access to consistent configuration values.

import os
import yaml
import platform
from pathlib import Path

class ConfigManager:
    """
    CODEX: Manages application configuration.
    CODEX: Loads settings from config.yaml and provides access methods.
    """
    
    def __init__(self, config_path=None):
        """
        CODEX: Initialize the configuration manager.
        
        Args:
            config_path (str, optional): Path to configuration file. Defaults to None.
        """
        # Set default config path if not provided
        if config_path is None:
            self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
        else:
            self.config_path = config_path
        
        # Load configuration
        self.config = self._load_config()
        
        # Apply platform-specific adjustments
        self._adjust_for_platform()
    
    def _load_config(self):
        """
        CODEX: Load configuration from YAML file.
        CODEX: If file doesn't exist, create default configuration.
        
        Returns:
            dict: Configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                return config
        except FileNotFoundError:
            # Create default configuration
            default_config = self._create_default_config()
            self._save_config(default_config)
            return default_config
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {str(e)}")
    
    def _create_default_config(self):
        """
        CODEX: Create default configuration settings.
        
        Returns:
            dict: Default configuration dictionary
        """
        return {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3.2",
                "system_prompt": "You are a financial advisor specializing in both American and Brazilian markets. Provide detailed, accurate investment advice based on the data provided.",
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "data_sources": {
                "update_frequency": 24,
                "cache_path": "./data/market_cache",
                "api_keys": {
                    "alpha_vantage": ""
                }
            },
            "markets": {
                "us": {
                    "indices": ["^GSPC", "^DJI", "^IXIC"],
                    "currency": "USD"
                },
                "brazil": {
                    "indices": ["^BVSP"],
                    "currency": "BRL"
                }
            },
            "investment": {
                "risk_profiles": {
                    "conservative": {
                        "stocks": 20,
                        "bonds": 60,
                        "cash": 20
                    },
                    "moderate": {
                        "stocks": 50,
                        "bonds": 40,
                        "cash": 10
                    },
                    "aggressive": {
                        "stocks": 80,
                        "bonds": 15,
                        "cash": 5
                    }
                },
                "inflation": {
                    "us": 2.5,
                    "brazil": 4.5
                }
            },
            "system": {
                "database": {
                    "path": "./data/finbot.db",
                    "backup_frequency": 168
                },
                "logging": {
                    "level": "INFO",
                    "file": "./logs/finbot.log",
                    "max_size": 10,
                    "backup_count": 5
                },
                "output": {
                    "color_scheme": "dark",
                    "detail_level": "medium"
                }
            }
        }
    
    def _save_config(self, config):
        """
        CODEX: Save configuration to YAML file.
        
        Args:
            config (dict): Configuration dictionary to save
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Write configuration
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False)
    
    def _adjust_for_platform(self):
        """
        CODEX: Adjust configuration based on platform (Windows/Linux).
        CODEX: Ensures cross-platform compatibility.
        """
        system = platform.system()
        
        # Convert paths to platform-specific format
        if system == "Windows":
            self.config["system"]["database"]["path"] = self.config["system"]["database"]["path"].replace("/", "\\")
            self.config["system"]["logging"]["file"] = self.config["system"]["logging"]["file"].replace("/", "\\")
            self.config["data_sources"]["cache_path"] = self.config["data_sources"]["cache_path"].replace("/", "\\")
        else:
            self.config["system"]["database"]["path"] = self.config["system"]["database"]["path"].replace("\\", "/")
            self.config["system"]["logging"]["file"] = self.config["system"]["logging"]["file"].replace("\\", "/")
            self.config["data_sources"]["cache_path"] = self.config["data_sources"]["cache_path"].replace("\\", "/")
    
    def get_ollama_config(self):
        """
        CODEX: Get Ollama configuration.
        
        Returns:
            dict: Ollama configuration
        """
        return self.config.get("ollama", {})
    
    def get_data_sources_config(self):
        """
        CODEX: Get data sources configuration.
        
        Returns:
            dict: Data sources configuration
        """
        return self.config.get("data_sources", {})
    
    def get_markets_config(self):
        """
        CODEX: Get markets configuration.
        
        Returns:
            dict: Markets configuration
        """
        return self.config.get("markets", {})
    
    def get_investment_config(self):
        """
        CODEX: Get investment configuration.
        
        Returns:
            dict: Investment configuration
        """
        return self.config.get("investment", {})
    
    def get_database_config(self):
        """
        CODEX: Get database configuration.
        
        Returns:
            dict: Database configuration
        """
        return self.config.get("system", {}).get("database", {})
    
    def get_logging_config(self):
        """
        CODEX: Get logging configuration.
        
        Returns:
            dict: Logging configuration
        """
        return self.config.get("system", {}).get("logging", {})
    
    def get_output_config(self):
        """
        CODEX: Get output formatting configuration.
        
        Returns:
            dict: Output configuration
        """
        return self.config.get("system", {}).get("output", {})
    
    def update_config(self, section, key, value):
        """
        CODEX: Update a specific configuration value.
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            value: New value
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Navigate to the specified section
            config_section = self.config
            sections = section.split('.')
            
            # Navigate to the nested section
            for s in sections[:-1]:
                if s not in config_section:
                    config_section[s] = {}
                config_section = config_section[s]
            
            # Update the value
            config_section[sections[-1]][key] = value
            
            # Save the updated configuration
            self._save_config(self.config)
            
            return True
        except Exception:
            return False
    
    def reset_to_defaults(self):
        """
        CODEX: Reset configuration to default values.
        
        Returns:
            bool: True if reset was successful, False otherwise
        """
        try:
            self.config = self._create_default_config()
            self._save_config(self.config)
            return True
        except Exception:
            return False
