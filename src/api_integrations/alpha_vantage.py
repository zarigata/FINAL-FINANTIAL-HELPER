#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# ALPHA VANTAGE API INTEGRATION v1.0
# CODEX: This module handles integration with Alpha Vantage API for US market data.
# CODEX: Provides reliable data fetching for stocks, bonds, and forex with robust error handling.

import os
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import threading
from pathlib import Path

class AlphaVantageAPI:
    """
    CODEX: Handles integration with Alpha Vantage API for US market data.
    CODEX: Provides methods for fetching stock, bond, and forex data with caching.
    """
    
    def __init__(self, api_key=None, base_url="https://www.alphavantage.co/query", cache_dir=None):
        """
        CODEX: Initialize the Alpha Vantage API client.
        
        Args:
            api_key (str, optional): Alpha Vantage API key. Defaults to None.
            base_url (str, optional): API base URL. Defaults to "https://www.alphavantage.co/query".
            cache_dir (str, optional): Directory for caching data. Defaults to None.
        """
        # Set API key from parameter, environment variable, or config file
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY", "")
        self.base_url = base_url
        
        # Set cache directory
        if cache_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.cache_dir = os.path.join(base_dir, "data", "market_cache", "alpha_vantage")
        else:
            self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Set up thread lock for API calls
        self.api_lock = threading.Lock()
        
        # API call counter and timestamp for rate limiting
        self.api_calls = 0
        self.api_call_reset_time = datetime.now()
        
        # Maximum API calls per minute (Alpha Vantage free tier: 5 calls per minute, 500 per day)
        self.max_calls_per_minute = 5
    
    def _make_api_request(self, params):
        """
        CODEX: Make an API request to Alpha Vantage with rate limiting.
        
        Args:
            params (dict): API request parameters
        
        Returns:
            dict: API response data
        """
        # Add API key to parameters
        params["apikey"] = self.api_key
        
        # Check if we need to wait for rate limit reset
        with self.api_lock:
            current_time = datetime.now()
            
            # Reset counter if a minute has passed
            if (current_time - self.api_call_reset_time).total_seconds() >= 60:
                self.api_calls = 0
                self.api_call_reset_time = current_time
            
            # Wait if we've reached the rate limit
            if self.api_calls >= self.max_calls_per_minute:
                wait_time = 60 - (current_time - self.api_call_reset_time).total_seconds()
                if wait_time > 0:
                    self.logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    # Reset counter after waiting
                    self.api_calls = 0
                    self.api_call_reset_time = datetime.now()
            
            # Increment API call counter
            self.api_calls += 1
        
        try:
            # Make the API request
            response = requests.get(self.base_url, params=params)
            
            # Check for successful response
            if response.status_code == 200:
                data = response.json()
                
                # Check for API error messages
                if "Error Message" in data:
                    self.logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                    return None
                
                return data
            else:
                self.logger.error(f"Alpha Vantage API request failed: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error making Alpha Vantage API request: {str(e)}")
            return None
    
    def _get_cache_path(self, function, symbol, interval=None, outputsize=None):
        """
        CODEX: Get the cache file path for a specific API request.
        
        Args:
            function (str): API function name
            symbol (str): Stock symbol
            interval (str, optional): Data interval. Defaults to None.
            outputsize (str, optional): Output size. Defaults to None.
        
        Returns:
            str: Cache file path
        """
        # Create a unique filename based on parameters
        filename = f"{symbol}_{function}"
        if interval:
            filename += f"_{interval}"
        if outputsize:
            filename += f"_{outputsize}"
        filename += ".json"
        
        return os.path.join(self.cache_dir, filename)
    
    def _save_to_cache(self, data, cache_path):
        """
        CODEX: Save data to cache file.
        
        Args:
            data (dict): Data to save
            cache_path (str): Cache file path
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp to data
            data_with_timestamp = {
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            # Save data to cache file
            with open(cache_path, "w") as f:
                json.dump(data_with_timestamp, f)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error saving data to cache: {str(e)}")
            return False
    
    def _load_from_cache(self, cache_path, max_age_hours=24):
        """
        CODEX: Load data from cache file if it exists and is not too old.
        
        Args:
            cache_path (str): Cache file path
            max_age_hours (int, optional): Maximum age of cache in hours. Defaults to 24.
        
        Returns:
            dict: Cached data or None if not available
        """
        try:
            # Check if cache file exists
            if not os.path.exists(cache_path):
                return None
            
            # Load data from cache file
            with open(cache_path, "r") as f:
                cached_data = json.load(f)
            
            # Check if data is too old
            timestamp = datetime.fromisoformat(cached_data["timestamp"])
            age = datetime.now() - timestamp
            
            if age > timedelta(hours=max_age_hours):
                self.logger.info(f"Cached data is too old ({age.total_seconds() / 3600:.1f} hours)")
                return None
            
            return cached_data["data"]
        
        except Exception as e:
            self.logger.error(f"Error loading data from cache: {str(e)}")
            return None
    
    def get_stock_data(self, symbol, interval="daily", outputsize="full", use_cache=True, max_cache_age_hours=24):
        """
        CODEX: Get stock data from Alpha Vantage.
        
        Args:
            symbol (str): Stock symbol
            interval (str, optional): Data interval (daily, weekly, monthly). Defaults to "daily".
            outputsize (str, optional): Output size (compact, full). Defaults to "full".
            use_cache (bool, optional): Whether to use cached data. Defaults to True.
            max_cache_age_hours (int, optional): Maximum age of cache in hours. Defaults to 24.
        
        Returns:
            pandas.DataFrame: Stock data
        """
        # Map interval to API function
        function_map = {
            "daily": "TIME_SERIES_DAILY",
            "weekly": "TIME_SERIES_WEEKLY",
            "monthly": "TIME_SERIES_MONTHLY"
        }
        
        function = function_map.get(interval.lower(), "TIME_SERIES_DAILY")
        
        # Check cache first if enabled
        if use_cache:
            cache_path = self._get_cache_path(function, symbol, interval, outputsize)
            cached_data = self._load_from_cache(cache_path, max_cache_age_hours)
            
            if cached_data is not None:
                self.logger.info(f"Using cached data for {symbol} ({interval})")
                return self._parse_stock_data(cached_data, symbol)
        
        # Prepare API request parameters
        params = {
            "function": function,
            "symbol": symbol,
            "outputsize": outputsize
        }
        
        # Make API request
        data = self._make_api_request(params)
        
        if data is None:
            self.logger.warning(f"Failed to fetch data for {symbol}. Trying to use cache regardless of age...")
            
            # Try to use cache regardless of age
            if use_cache:
                cache_path = self._get_cache_path(function, symbol, interval, outputsize)
                cached_data = self._load_from_cache(cache_path, max_age_hours=float('inf'))
                
                if cached_data is not None:
                    self.logger.info(f"Using expired cached data for {symbol} ({interval})")
                    return self._parse_stock_data(cached_data, symbol)
            
            return None
        
        # Save to cache
        if use_cache:
            cache_path = self._get_cache_path(function, symbol, interval, outputsize)
            self._save_to_cache(data, cache_path)
        
        # Parse and return data
        return self._parse_stock_data(data, symbol)
    
    def _parse_stock_data(self, data, symbol):
        """
        CODEX: Parse stock data from Alpha Vantage response.
        
        Args:
            data (dict): Alpha Vantage response data
            symbol (str): Stock symbol
        
        Returns:
            pandas.DataFrame: Parsed stock data
        """
        try:
            # Get the time series data
            time_series_key = [key for key in data.keys() if "Time Series" in key]
            
            if not time_series_key:
                self.logger.error(f"No time series data found for {symbol}")
                return None
            
            time_series = data[time_series_key[0]]
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient="index")
            
            # Rename columns
            df.columns = [col.split(". ")[1] if ". " in col else col for col in df.columns]
            df.columns = [col.lower() for col in df.columns]
            
            # Convert index to datetime
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Convert columns to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
            
            # Add symbol column
            df["symbol"] = symbol
            
            # Add date column
            df["date"] = df.index
            
            # Rename columns to match expected format
            column_map = {
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
                "symbol": "symbol",
                "date": "Date"
            }
            
            df = df.rename(columns=column_map)
            
            # Add market column
            df["market"] = "US"
            
            # Add data_type column
            df["data_type"] = "stock"
            
            # Add last_updated column
            df["last_updated"] = datetime.now().isoformat()
            
            return df
        
        except Exception as e:
            self.logger.error(f"Error parsing stock data for {symbol}: {str(e)}")
            return None
    
    def get_forex_data(self, from_currency, to_currency="USD", interval="daily", outputsize="full", use_cache=True, max_cache_age_hours=24):
        """
        CODEX: Get forex data from Alpha Vantage.
        
        Args:
            from_currency (str): From currency code
            to_currency (str, optional): To currency code. Defaults to "USD".
            interval (str, optional): Data interval (daily, weekly, monthly). Defaults to "daily".
            outputsize (str, optional): Output size (compact, full). Defaults to "full".
            use_cache (bool, optional): Whether to use cached data. Defaults to True.
            max_cache_age_hours (int, optional): Maximum age of cache in hours. Defaults to 24.
        
        Returns:
            pandas.DataFrame: Forex data
        """
        # Map interval to API function
        function_map = {
            "daily": "FX_DAILY",
            "weekly": "FX_WEEKLY",
            "monthly": "FX_MONTHLY"
        }
        
        function = function_map.get(interval.lower(), "FX_DAILY")
        
        # Create symbol for cache
        symbol = f"{from_currency}{to_currency}"
        
        # Check cache first if enabled
        if use_cache:
            cache_path = self._get_cache_path(function, symbol, interval, outputsize)
            cached_data = self._load_from_cache(cache_path, max_cache_age_hours)
            
            if cached_data is not None:
                self.logger.info(f"Using cached data for {symbol} ({interval})")
                return self._parse_forex_data(cached_data, from_currency, to_currency)
        
        # Prepare API request parameters
        params = {
            "function": function,
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": outputsize
        }
        
        # Make API request
        data = self._make_api_request(params)
        
        if data is None:
            self.logger.warning(f"Failed to fetch forex data for {symbol}. Trying to use cache regardless of age...")
            
            # Try to use cache regardless of age
            if use_cache:
                cache_path = self._get_cache_path(function, symbol, interval, outputsize)
                cached_data = self._load_from_cache(cache_path, max_age_hours=float('inf'))
                
                if cached_data is not None:
                    self.logger.info(f"Using expired cached data for {symbol} ({interval})")
                    return self._parse_forex_data(cached_data, from_currency, to_currency)
            
            return None
        
        # Save to cache
        if use_cache:
            cache_path = self._get_cache_path(function, symbol, interval, outputsize)
            self._save_to_cache(data, cache_path)
        
        # Parse and return data
        return self._parse_forex_data(data, from_currency, to_currency)
    
    def _parse_forex_data(self, data, from_currency, to_currency):
        """
        CODEX: Parse forex data from Alpha Vantage response.
        
        Args:
            data (dict): Alpha Vantage response data
            from_currency (str): From currency code
            to_currency (str): To currency code
        
        Returns:
            pandas.DataFrame: Parsed forex data
        """
        try:
            # Get the time series data
            time_series_key = [key for key in data.keys() if "Time Series" in key]
            
            if not time_series_key:
                self.logger.error(f"No time series data found for {from_currency}/{to_currency}")
                return None
            
            time_series = data[time_series_key[0]]
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient="index")
            
            # Rename columns
            df.columns = [col.split(". ")[1] if ". " in col else col for col in df.columns]
            df.columns = [col.lower() for col in df.columns]
            
            # Convert index to datetime
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Convert columns to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
            
            # Add symbol column
            df["symbol"] = f"{from_currency}{to_currency}"
            
            # Add date column
            df["date"] = df.index
            
            # Rename columns to match expected format
            column_map = {
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "symbol": "symbol",
                "date": "Date"
            }
            
            df = df.rename(columns=column_map)
            
            # Add market column
            df["market"] = "FOREX"
            
            # Add data_type column
            df["data_type"] = "forex"
            
            # Add last_updated column
            df["last_updated"] = datetime.now().isoformat()
            
            # Add Volume column (not provided by Alpha Vantage for forex)
            df["Volume"] = 0
            
            return df
        
        except Exception as e:
            self.logger.error(f"Error parsing forex data for {from_currency}/{to_currency}: {str(e)}")
            return None
    
    def get_treasury_yield_data(self, maturity="10year", interval="daily", use_cache=True, max_cache_age_hours=24):
        """
        CODEX: Get US Treasury yield data from Alpha Vantage.
        
        Args:
            maturity (str, optional): Bond maturity (3month, 2year, 5year, 7year, 10year, 30year). Defaults to "10year".
            interval (str, optional): Data interval (daily, weekly, monthly). Defaults to "daily".
            use_cache (bool, optional): Whether to use cached data. Defaults to True.
            max_cache_age_hours (int, optional): Maximum age of cache in hours. Defaults to 24.
        
        Returns:
            pandas.DataFrame: Treasury yield data
        """
        function = "TREASURY_YIELD"
        
        # Check cache first if enabled
        if use_cache:
            cache_path = self._get_cache_path(function, maturity, interval)
            cached_data = self._load_from_cache(cache_path, max_cache_age_hours)
            
            if cached_data is not None:
                self.logger.info(f"Using cached data for Treasury {maturity} ({interval})")
                return self._parse_treasury_data(cached_data, maturity)
        
        # Prepare API request parameters
        params = {
            "function": function,
            "interval": interval,
            "maturity": maturity
        }
        
        # Make API request
        data = self._make_api_request(params)
        
        if data is None:
            self.logger.warning(f"Failed to fetch Treasury data for {maturity}. Trying to use cache regardless of age...")
            
            # Try to use cache regardless of age
            if use_cache:
                cache_path = self._get_cache_path(function, maturity, interval)
                cached_data = self._load_from_cache(cache_path, max_age_hours=float('inf'))
                
                if cached_data is not None:
                    self.logger.info(f"Using expired cached data for Treasury {maturity} ({interval})")
                    return self._parse_treasury_data(cached_data, maturity)
            
            return None
        
        # Save to cache
        if use_cache:
            cache_path = self._get_cache_path(function, maturity, interval)
            self._save_to_cache(data, cache_path)
        
        # Parse and return data
        return self._parse_treasury_data(data, maturity)
    
    def _parse_treasury_data(self, data, maturity):
        """
        CODEX: Parse treasury data from Alpha Vantage response.
        
        Args:
            data (dict): Alpha Vantage response data
            maturity (str): Bond maturity
        
        Returns:
            pandas.DataFrame: Parsed treasury data
        """
        try:
            # Get the data
            if "data" not in data:
                self.logger.error(f"No data found for Treasury {maturity}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data["data"])
            
            # Convert date to datetime
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            
            # Convert value to numeric
            df["value"] = pd.to_numeric(df["value"])
            
            # Create a stock-like DataFrame
            result = pd.DataFrame({
                "Date": df["date"],
                "Open": df["value"],
                "High": df["value"],
                "Low": df["value"],
                "Close": df["value"],
                "Volume": 0,
                "symbol": f"TREASURY_{maturity.upper()}",
                "market": "US",
                "data_type": "bond",
                "last_updated": datetime.now().isoformat()
            })
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error parsing Treasury data for {maturity}: {str(e)}")
            return None
