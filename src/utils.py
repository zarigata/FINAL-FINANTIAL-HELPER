#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# UTILITIES MODULE v1.0
# CODEX: This module provides utility functions used across the application.
# CODEX: Includes logging setup, directory creation, and other helper functions.

import os
import logging
import platform
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

def setup_logging(logging_config):
    """
    CODEX: Configure application logging based on configuration.
    CODEX: Sets up file and console handlers with appropriate formatting.
    
    Args:
        logging_config (dict): Logging configuration dictionary
    """
    # Get configuration values with defaults
    log_level = getattr(logging, logging_config.get('level', 'INFO'))
    log_file = logging_config.get('file', './logs/finbot.log')
    max_size = logging_config.get('max_size', 10) * 1024 * 1024  # Convert MB to bytes
    backup_count = logging_config.get('backup_count', 5)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create file handler
    try:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {str(e)}")
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    logging.info("Logging initialized")

def create_directories():
    """
    CODEX: Create necessary application directories if they don't exist.
    CODEX: Ensures all required paths are available before application starts.
    """
    # Get base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define required directories
    directories = [
        os.path.join(base_dir, "data"),
        os.path.join(base_dir, "data", "market_cache"),
        os.path.join(base_dir, "logs"),
    ]
    
    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def format_currency(amount, currency="USD"):
    """
    CODEX: Format amount as currency string.
    
    Args:
        amount (float): Amount to format
        currency (str, optional): Currency code. Defaults to "USD".
    
    Returns:
        str: Formatted currency string
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "BRL":
        return f"R${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def calculate_compound_interest(principal, rate, time, compounds_per_year=1):
    """
    CODEX: Calculate compound interest over time.
    
    Args:
        principal (float): Initial investment amount
        rate (float): Annual interest rate (as decimal, e.g., 0.05 for 5%)
        time (int): Time period in years
        compounds_per_year (int, optional): Number of times interest compounds per year. Defaults to 1.
    
    Returns:
        float: Final amount after compound interest
    """
    return principal * (1 + rate/compounds_per_year) ** (compounds_per_year * time)

def calculate_inflation_adjusted_return(nominal_return, inflation_rate, time_years):
    """
    CODEX: Calculate inflation-adjusted return over time.
    
    Args:
        nominal_return (float): Nominal return rate (as decimal)
        inflation_rate (float): Inflation rate (as decimal)
        time_years (int): Time period in years
    
    Returns:
        float: Real (inflation-adjusted) return rate
    """
    real_return = (1 + nominal_return) / (1 + inflation_rate) - 1
    return (1 + real_return) ** time_years - 1

def get_platform_info():
    """
    CODEX: Get information about the current platform.
    
    Returns:
        dict: Dictionary with platform information
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

def is_valid_market(market):
    """
    CODEX: Check if market code is valid.
    
    Args:
        market (str): Market code to check
    
    Returns:
        bool: True if valid, False otherwise
    """
    return market in ["US", "BR", "BOTH"]

def is_valid_investment_type(inv_type):
    """
    CODEX: Check if investment type is valid.
    
    Args:
        inv_type (str): Investment type to check
    
    Returns:
        bool: True if valid, False otherwise
    """
    return inv_type in ["stocks", "bonds", "savings", "mixed", "market"]

def is_valid_risk_profile(risk):
    """
    CODEX: Check if risk profile is valid.
    
    Args:
        risk (str): Risk profile to check
    
    Returns:
        bool: True if valid, False otherwise
    """
    return risk in ["conservative", "moderate", "aggressive"]

def get_current_timestamp():
    """
    CODEX: Get current timestamp in ISO format.
    
    Returns:
        str: Current timestamp
    """
    return datetime.now().isoformat()
