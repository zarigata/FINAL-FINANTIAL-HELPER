#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# B3 API INTEGRATION v1.0
# CODEX: This module handles integration with B3 (Brazilian Stock Exchange) for market data.
# CODEX: Provides data fetching for stocks, bonds (Tesouro Direto), and FIIs with robust error handling.

import os
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import threading
from pathlib import Path
from bs4 import BeautifulSoup
import sqlite3

# Import internal modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.ai import AIEngine

class B3API:
    """
    CODEX: Handles integration with B3 (Brazilian Stock Exchange) for market data.
    CODEX: Provides methods for fetching stock, bond, and FII data with caching.
    """
    
    def __init__(self, cache_dir=None, db_path=None):
        """
        CODEX: Initialize the B3 API client.
        
        Args:
            cache_dir (str, optional): Directory for caching data. Defaults to None.
            db_path (str, optional): Path to SQLite database. Defaults to None.
        """
        # Set base URLs
        self.base_url = "https://www.b3.com.br"
        self.api_url = "https://cotacao.b3.com.br/mds/api/v1/DailyFluctuationHistory"
        
        # Set cache directory
        if cache_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.cache_dir = os.path.join(base_dir, "data", "market_cache", "b3")
        else:
            self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set database path
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(base_dir, "data", "finbot.db")
        else:
            self.db_path = db_path
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Set up thread lock for API calls
        self.api_lock = threading.Lock()
        
        # API call counter and timestamp for rate limiting
        self.api_calls = 0
        self.api_call_reset_time = datetime.now()
        
        # Initialize database
        self._init_database()
        
        # Initialize AI Engine for web search
        try:
            self.ai_engine = AIEngine()
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Engine: {str(e)}")
            self.ai_engine = None
    
    def _init_database(self):
        """
        CODEX: Initialize the SQLite database for storing B3 data.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS b3_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    market TEXT,
                    data_type TEXT,
                    last_updated TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS b3_fiis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    dividend_yield REAL,
                    market TEXT,
                    data_type TEXT,
                    last_updated TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS b3_bonds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    date TEXT,
                    price REAL,
                    yield REAL,
                    maturity TEXT,
                    market TEXT,
                    data_type TEXT,
                    last_updated TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS currency_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_currency TEXT,
                    to_currency TEXT,
                    date TEXT,
                    rate REAL,
                    last_updated TEXT
                )
            ''')
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
    
    def _make_api_request(self, url, params=None, headers=None):
        """
        CODEX: Make an API request to B3 with rate limiting.
        
        Args:
            url (str): API URL
            params (dict, optional): API request parameters. Defaults to None.
            headers (dict, optional): API request headers. Defaults to None.
        
        Returns:
            dict: API response data
        """
        # Check if we need to wait for rate limit reset
        with self.api_lock:
            current_time = datetime.now()
            
            # Reset counter if a minute has passed
            if (current_time - self.api_call_reset_time).total_seconds() >= 60:
                self.api_calls = 0
                self.api_call_reset_time = current_time
            
            # Wait if we've reached the rate limit (10 calls per minute)
            if self.api_calls >= 10:
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
            # Set default headers if not provided
            if headers is None:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
                    "Origin": "https://www.b3.com.br",
                    "Referer": "https://www.b3.com.br/"
                }
            
            # Make the API request
            response = requests.get(url, params=params, headers=headers)
            
            # Check for successful response
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    return response.text
            else:
                self.logger.error(f"B3 API request failed: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error making B3 API request: {str(e)}")
            return None
    
    def _get_cache_path(self, data_type, symbol):
        """
        CODEX: Get the cache file path for a specific API request.
        
        Args:
            data_type (str): Data type (stocks, fiis, bonds)
            symbol (str): Stock symbol
        
        Returns:
            str: Cache file path
        """
        # Create a unique filename based on parameters
        filename = f"{symbol}_{data_type}.json"
        
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
    
    def _save_to_database(self, data, table_name):
        """
        CODEX: Save data to SQLite database.
        
        Args:
            data (pandas.DataFrame): Data to save
            table_name (str): Table name
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # Save data to database
            data.to_sql(table_name, conn, if_exists="append", index=False)
            
            # Close connection
            conn.close()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error saving data to database: {str(e)}")
            return False
    
    def _load_from_database(self, table_name, symbol=None, start_date=None, end_date=None):
        """
        CODEX: Load data from SQLite database.
        
        Args:
            table_name (str): Table name
            symbol (str, optional): Stock symbol. Defaults to None.
            start_date (str, optional): Start date (YYYY-MM-DD). Defaults to None.
            end_date (str, optional): End date (YYYY-MM-DD). Defaults to None.
        
        Returns:
            pandas.DataFrame: Data from database
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # Build query
            query = f"SELECT * FROM {table_name}"
            conditions = []
            
            if symbol:
                conditions.append(f"symbol = '{symbol}'")
            
            if start_date:
                conditions.append(f"date >= '{start_date}'")
            
            if end_date:
                conditions.append(f"date <= '{end_date}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # Execute query
            data = pd.read_sql_query(query, conn)
            
            # Close connection
            conn.close()
            
            return data
        
        except Exception as e:
            self.logger.error(f"Error loading data from database: {str(e)}")
            return None
    
    def search_open_source_scripts(self, query="Python scripts for B3 API integration"):
        """
        CODEX: Search for open-source scripts using Ollama.
        
        Args:
            query (str, optional): Search query. Defaults to "Python scripts for B3 API integration".
        
        Returns:
            str: Search results
        """
        if self.ai_engine is None:
            self.logger.error("AI Engine not initialized")
            return None
        
        try:
            # Use Ollama to search for open-source scripts
            result = self.ai_engine.query(query)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error searching for open-source scripts: {str(e)}")
            return None
    
    def get_stock_data(self, symbol, start_date=None, end_date=None, use_cache=True, max_cache_age_hours=24):
        """
        CODEX: Get stock data from B3.
        
        Args:
            symbol (str): Stock symbol (e.g., PETR4, VALE3)
            start_date (str, optional): Start date (YYYY-MM-DD). Defaults to None.
            end_date (str, optional): End date (YYYY-MM-DD). Defaults to None.
            use_cache (bool, optional): Whether to use cached data. Defaults to True.
            max_cache_age_hours (int, optional): Maximum age of cache in hours. Defaults to 24.
        
        Returns:
            pandas.DataFrame: Stock data
        """
        # Standardize symbol format
        symbol = symbol.upper()
        
        # Check cache first if enabled
        if use_cache:
            cache_path = self._get_cache_path("stocks", symbol)
            cached_data = self._load_from_cache(cache_path, max_cache_age_hours)
            
            if cached_data is not None:
                self.logger.info(f"Using cached data for {symbol}")
                return pd.DataFrame(cached_data)
        
        # Try to load from database
        db_data = self._load_from_database("b3_stocks", symbol, start_date, end_date)
        
        if db_data is not None and not db_data.empty:
            self.logger.info(f"Using database data for {symbol}")
            return db_data
        
        # Prepare API request parameters
        params = {
            "language": "pt-br",
            "symbol": symbol
        }
        
        # Make API request
        data = self._make_api_request(self.api_url, params)
        
        if data is None or not isinstance(data, dict) or "TradgFlr" not in data:
            self.logger.warning(f"Failed to fetch data for {symbol}. Trying alternative method...")
            
            # Try alternative method: web scraping
            data = self._scrape_stock_data(symbol)
            
            if data is None:
                self.logger.warning(f"Failed to fetch data for {symbol} using alternative method. Trying to use cache regardless of age...")
                
                # Try to use cache regardless of age
                if use_cache:
                    cache_path = self._get_cache_path("stocks", symbol)
                    cached_data = self._load_from_cache(cache_path, max_age_hours=float('inf'))
                    
                    if cached_data is not None:
                        self.logger.info(f"Using expired cached data for {symbol}")
                        return pd.DataFrame(cached_data)
                
                return None
        
        # Parse data
        parsed_data = self._parse_stock_data(data, symbol)
        
        if parsed_data is None:
            self.logger.error(f"Failed to parse data for {symbol}")
            return None
        
        # Save to cache
        if use_cache:
            cache_path = self._get_cache_path("stocks", symbol)
            self._save_to_cache(parsed_data.to_dict("records"), cache_path)
        
        # Save to database
        self._save_to_database(parsed_data, "b3_stocks")
        
        return parsed_data
    
    def _scrape_stock_data(self, symbol):
        """
        CODEX: Scrape stock data from B3 website.
        
        Args:
            symbol (str): Stock symbol
        
        Returns:
            dict: Scraped data
        """
        try:
            # Build URL
            url = f"https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/cotacoes/cotacoes-de-ativos/?symbol={symbol}"
            
            # Make request
            response = requests.get(url)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to scrape data for {symbol}: {response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract data
            data = {}
            data["TradgFlr"] = {"scty": {"SctyQtn": []}}
            
            # Find the stock price table
            table = soup.find("table", class_="table-responsive")
            
            if table is None:
                self.logger.error(f"Failed to find stock price table for {symbol}")
                return None
            
            # Extract rows
            rows = table.find_all("tr")
            
            for row in rows[1:]:  # Skip header row
                cols = row.find_all("td")
                
                if len(cols) >= 5:
                    date_str = cols[0].text.strip()
                    open_price = float(cols[1].text.strip().replace(".", "").replace(",", "."))
                    high_price = float(cols[2].text.strip().replace(".", "").replace(",", "."))
                    low_price = float(cols[3].text.strip().replace(".", "").replace(",", "."))
                    close_price = float(cols[4].text.strip().replace(".", "").replace(",", "."))
                    
                    # Convert date
                    date = datetime.strptime(date_str, "%d/%m/%Y")
                    
                    # Add to data
                    data["TradgFlr"]["scty"]["SctyQtn"].append({
                        "date": date.strftime("%Y-%m-%d"),
                        "opnPric": open_price,
                        "maxPric": high_price,
                        "minPric": low_price,
                        "closPric": close_price,
                        "tradQty": 0  # Volume not available
                    })
            
            return data
        
        except Exception as e:
            self.logger.error(f"Error scraping stock data for {symbol}: {str(e)}")
            return None
    
    def _parse_stock_data(self, data, symbol):
        """
        CODEX: Parse stock data from B3 response.
        
        Args:
            data (dict): B3 response data
            symbol (str): Stock symbol
        
        Returns:
            pandas.DataFrame: Parsed stock data
        """
        try:
            # Extract quotes
            quotes = data["TradgFlr"]["scty"]["SctyQtn"]
            
            if not quotes:
                self.logger.error(f"No quotes found for {symbol}")
                return None
            
            # Convert to DataFrame
            records = []
            
            for quote in quotes:
                record = {
                    "symbol": symbol,
                    "date": quote.get("date", ""),
                    "open": quote.get("opnPric", 0),
                    "high": quote.get("maxPric", 0),
                    "low": quote.get("minPric", 0),
                    "close": quote.get("closPric", 0),
                    "volume": quote.get("tradQty", 0),
                    "market": "BR",
                    "data_type": "stock",
                    "last_updated": datetime.now().isoformat()
                }
                
                records.append(record)
            
            df = pd.DataFrame(records)
            
            # Convert date to datetime
            df["date"] = pd.to_datetime(df["date"])
            
            # Sort by date
            df = df.sort_values("date")
            
            # Rename columns to match expected format
            column_map = {
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
                "date": "Date"
            }
            
            df = df.rename(columns=column_map)
            
            return df
        
        except Exception as e:
            self.logger.error(f"Error parsing stock data for {symbol}: {str(e)}")
            return None
    
    def get_fii_data(self, symbol, start_date=None, end_date=None, use_cache=True, max_cache_age_hours=24):
        """
        CODEX: Get FII (Real Estate Investment Fund) data from B3.
        
        Args:
            symbol (str): FII symbol (e.g., HGLG11, KNRI11)
            start_date (str, optional): Start date (YYYY-MM-DD). Defaults to None.
            end_date (str, optional): End date (YYYY-MM-DD). Defaults to None.
            use_cache (bool, optional): Whether to use cached data. Defaults to True.
            max_cache_age_hours (int, optional): Maximum age of cache in hours. Defaults to 24.
        
        Returns:
            pandas.DataFrame: FII data
        """
        # FIIs are treated as stocks in B3 API
        stock_data = self.get_stock_data(symbol, start_date, end_date, use_cache, max_cache_age_hours)
        
        if stock_data is None:
            return None
        
        # Update data type
        stock_data["data_type"] = "fii"
        
        # Try to get dividend yield
        try:
            # This would require additional scraping for dividend yield
            # For now, we'll just return the stock data
            pass
        except Exception as e:
            self.logger.error(f"Error getting dividend yield for {symbol}: {str(e)}")
        
        return stock_data
