#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# DATA MANAGEMENT MODULE v1.0
# CODEX: This module handles all data operations for the FinBot application.
# CODEX: Includes fetching, storing, and retrieving market data from various sources.

import os
import json
import logging
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
import random

class DataManager:
    """
    CODEX: Manages all data operations for the FinBot application.
    CODEX: Handles database connections, market data fetching, and caching.
    """
    
    def __init__(self, db_config):
        """
        CODEX: Initialize the data manager.
        
        Args:
            db_config (dict): Database configuration
        """
        self.db_path = db_config.get('path', './data/finbot.db')
        self.backup_frequency = db_config.get('backup_frequency', 168)  # Hours
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def initialize_database(self):
        """
        CODEX: Initialize the database with required tables.
        CODEX: Creates tables if they don't exist.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create market data table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                data_type TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                UNIQUE(symbol, date, data_type)
            )
            ''')
            
            # Create portfolio table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                risk_profile TEXT NOT NULL,
                created_date TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                UNIQUE(name)
            )
            ''')
            
            # Create portfolio assets table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                allocation_percentage REAL NOT NULL,
                purchase_price REAL,
                purchase_date TEXT,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
                UNIQUE(portfolio_id, symbol)
            )
            ''')
            
            # Create economic indicators table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS economic_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL,
                indicator_name TEXT NOT NULL,
                date TEXT NOT NULL,
                value REAL NOT NULL,
                last_updated TEXT NOT NULL,
                UNIQUE(country, indicator_name, date)
            )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            return False
    
    def backup_database(self):
        """
        CODEX: Create a backup of the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"finbot_backup_{timestamp}.db")
            
            # Copy database to backup location
            conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)
            
            conn.backup(backup_conn)
            
            backup_conn.close()
            conn.close()
            
            self.logger.info(f"Database backup created at {backup_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error backing up database: {str(e)}")
            return False
    
    def fetch_stock_data(self, symbol, market, period="1y"):
        """
        CODEX: Fetch stock data from Yahoo Finance.
        
        Args:
            symbol (str): Stock symbol
            market (str): Market (US or BR)
            period (str, optional): Time period. Defaults to "1y".
        
        Returns:
            pandas.DataFrame: Stock data
        """
        try:
            # Add market suffix for Brazilian stocks if needed
            if market == "BR" and not symbol.endswith(".SA"):
                symbol = f"{symbol}.SA"
            
            # Fetch data from Yahoo Finance
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)
            
            # Reset index to make date a column
            data = data.reset_index()
            
            # Add metadata columns
            data['symbol'] = symbol
            data['market'] = market
            data['data_type'] = 'stock'
            data['last_updated'] = datetime.now().isoformat()
            
            # Store data in database
            self._store_market_data(data)
            
            return data
        
        except Exception as e:
            self.logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            
            # Try to get cached data if available
            cached_data = self.get_cached_market_data(symbol, market, 'stock')
            if cached_data is not None:
                self.logger.info(f"Using cached data for {symbol}")
                return cached_data
            
            return None
    
    def fetch_bond_data(self, symbol, market):
        """
        CODEX: Fetch bond data.
        CODEX: For US bonds, uses Yahoo Finance.
        CODEX: For Brazilian bonds, uses specialized sources.
        
        Args:
            symbol (str): Bond symbol
            market (str): Market (US or BR)
        
        Returns:
            pandas.DataFrame: Bond data
        """
        try:
            if market == "US":
                # For US bonds, use Yahoo Finance
                bond = yf.Ticker(symbol)
                data = bond.history(period="1y")
                
                # Reset index to make date a column
                data = data.reset_index()
                
            elif market == "BR":
                # For Brazilian bonds, we would need to implement a custom scraper
                # This is a placeholder for demonstration
                # In a real implementation, this would fetch data from Tesouro Direto or similar sources
                
                # Create a dummy dataframe with estimated data
                dates = pd.date_range(end=datetime.now(), periods=365)
                data = pd.DataFrame({
                    'Date': dates,
                    'Open': np.linspace(100, 110, 365) + np.random.normal(0, 0.5, 365),
                    'High': np.linspace(100, 110, 365) + np.random.normal(0, 0.7, 365),
                    'Low': np.linspace(100, 110, 365) + np.random.normal(0, 0.3, 365),
                    'Close': np.linspace(100, 110, 365) + np.random.normal(0, 0.5, 365),
                    'Volume': np.random.randint(1000, 10000, 365)
                })
            
            # Add metadata columns
            data['symbol'] = symbol
            data['market'] = market
            data['data_type'] = 'bond'
            data['last_updated'] = datetime.now().isoformat()
            
            # Store data in database
            self._store_market_data(data)
            
            return data
        
        except Exception as e:
            self.logger.error(f"Error fetching bond data for {symbol}: {str(e)}")
            
            # Try to get cached data if available
            cached_data = self.get_cached_market_data(symbol, market, 'bond')
            if cached_data is not None:
                self.logger.info(f"Using cached data for {symbol}")
                return cached_data
            
            return None
    
    def fetch_savings_data(self, market):
        """
        CODEX: Fetch savings account data.
        CODEX: For US, fetches CD rates.
        CODEX: For Brazil, fetches Poupança rates.
        
        Args:
            market (str): Market (US or BR)
        
        Returns:
            pandas.DataFrame: Savings data
        """
        try:
            # This is a placeholder for demonstration
            # In a real implementation, this would fetch data from appropriate sources
            
            # Create a dummy dataframe with estimated data
            dates = pd.date_range(end=datetime.now(), periods=365)
            
            if market == "US":
                # Approximate CD rates
                symbol = "US_CD_RATES"
                base_rate = 0.04  # 4% annual
                
                data = pd.DataFrame({
                    'Date': dates,
                    'Open': [base_rate] * 365,
                    'High': [base_rate] * 365,
                    'Low': [base_rate] * 365,
                    'Close': [base_rate + (i * 0.0001) for i in range(365)],
                    'Volume': [0] * 365
                })
            
            elif market == "BR":
                # Approximate Poupança rates
                symbol = "BR_POUPANCA"
                base_rate = 0.06  # 6% annual
                
                data = pd.DataFrame({
                    'Date': dates,
                    'Open': [base_rate] * 365,
                    'High': [base_rate] * 365,
                    'Low': [base_rate] * 365,
                    'Close': [base_rate + (i * 0.0001) for i in range(365)],
                    'Volume': [0] * 365
                })
            
            # Add metadata columns
            data['symbol'] = symbol
            data['market'] = market
            data['data_type'] = 'savings'
            data['last_updated'] = datetime.now().isoformat()
            
            # Store data in database
            self._store_market_data(data)
            
            return data
        
        except Exception as e:
            self.logger.error(f"Error fetching savings data for {market}: {str(e)}")
            
            # Try to get cached data if available
            symbol = "US_CD_RATES" if market == "US" else "BR_POUPANCA"
            cached_data = self.get_cached_market_data(symbol, market, 'savings')
            if cached_data is not None:
                self.logger.info(f"Using cached data for {symbol}")
                return cached_data
            
            return None
    
    def fetch_economic_indicators(self, country):
        """
        CODEX: Fetch economic indicators for a country.
        
        Args:
            country (str): Country code (US or BR)
        
        Returns:
            dict: Dictionary of economic indicators
        """
        try:
            # This is a placeholder for demonstration
            # In a real implementation, this would fetch data from appropriate sources
            
            indicators = {}
            current_date = datetime.now().isoformat()
            
            if country == "US":
                # Approximate US economic indicators
                indicators = {
                    "inflation_rate": 2.5,
                    "interest_rate": 4.5,
                    "gdp_growth": 2.0,
                    "unemployment_rate": 3.8
                }
            
            elif country == "BR":
                # Approximate Brazilian economic indicators
                indicators = {
                    "inflation_rate": 4.5,
                    "interest_rate": 10.5,
                    "gdp_growth": 1.5,
                    "unemployment_rate": 8.5
                }
            
            # Store indicators in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for indicator_name, value in indicators.items():
                cursor.execute('''
                INSERT OR REPLACE INTO economic_indicators
                (country, indicator_name, date, value, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ''', (country, indicator_name, current_date, value, current_date))
            
            conn.commit()
            conn.close()
            
            return indicators
        
        except Exception as e:
            self.logger.error(f"Error fetching economic indicators for {country}: {str(e)}")
            
            # Try to get cached data if available
            cached_indicators = self.get_cached_economic_indicators(country)
            if cached_indicators:
                self.logger.info(f"Using cached economic indicators for {country}")
                return cached_indicators
            
            return None
    
    def _store_market_data(self, data):
        """
        CODEX: Store market data in the database.
        
        Args:
            data (pandas.DataFrame): Market data to store
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Prepare data for insertion
            for _, row in data.iterrows():
                # Extract values
                symbol = row['symbol']
                market = row['market']
                date = row['Date'].isoformat() if isinstance(row['Date'], datetime) else row['Date']
                open_price = row.get('Open', None)
                high_price = row.get('High', None)
                low_price = row.get('Low', None)
                close_price = row.get('Close', None)
                volume = row.get('Volume', 0)
                data_type = row['data_type']
                last_updated = row['last_updated']
                
                # Insert or replace data
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO market_data
                (symbol, market, date, open, high, low, close, volume, data_type, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, market, date, open_price, high_price, low_price, close_price, volume, data_type, last_updated))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing market data: {str(e)}")
    
    def get_cached_market_data(self, symbol, market, data_type, days=365):
        """
        CODEX: Get cached market data from the database.
        
        Args:
            symbol (str): Symbol to retrieve
            market (str): Market (US or BR)
            data_type (str): Type of data (stock, bond, savings)
            days (int, optional): Number of days of data to retrieve. Defaults to 365.
        
        Returns:
            pandas.DataFrame: Cached market data or None if not available
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query data
            query = '''
            SELECT * FROM market_data
            WHERE symbol = ? AND market = ? AND data_type = ?
            AND date BETWEEN ? AND ?
            ORDER BY date ASC
            '''
            
            data = pd.read_sql_query(
                query,
                conn,
                params=(symbol, market, data_type, start_date.isoformat(), end_date.isoformat())
            )
            
            conn.close()
            
            if len(data) > 0:
                return data
            else:
                return None
        
        except Exception as e:
            self.logger.error(f"Error retrieving cached market data: {str(e)}")
            return None
    
    def get_cached_economic_indicators(self, country):
        """
        CODEX: Get cached economic indicators from the database.
        
        Args:
            country (str): Country code (US or BR)
        
        Returns:
            dict: Dictionary of economic indicators or None if not available
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query latest indicators
            cursor.execute('''
            SELECT indicator_name, value
            FROM economic_indicators
            WHERE country = ?
            GROUP BY indicator_name
            HAVING date = MAX(date)
            ''', (country,))
            
            results = cursor.fetchall()
            conn.close()
            
            if results:
                return {name: value for name, value in results}
            else:
                return None
        
        except Exception as e:
            self.logger.error(f"Error retrieving cached economic indicators: {str(e)}")
            return None
    
    def update_market_data(self, market="BOTH", force=False):
        """
        CODEX: Update market data for specified markets.
        
        Args:
            market (str, optional): Market to update (US, BR, or BOTH). Defaults to "BOTH".
            force (bool, optional): Force update even if data is recent. Defaults to False.
        
        Returns:
            dict: Update status for each market
        """
        update_status = {}
        
        try:
            # Determine which markets to update
            markets_to_update = []
            if market == "US" or market == "BOTH":
                markets_to_update.append("US")
            if market == "BR" or market == "BOTH":
                markets_to_update.append("BR")
            
            for mkt in markets_to_update:
                # Update stock indices
                indices = ["^GSPC", "^DJI", "^IXIC"] if mkt == "US" else ["^BVSP"]
                for index in indices:
                    data = self.fetch_stock_data(index, mkt)
                    update_status[f"{mkt}_{index}"] = "Updated" if data is not None else "Failed"
                
                # Update economic indicators
                indicators = self.fetch_economic_indicators(mkt)
                update_status[f"{mkt}_indicators"] = "Updated" if indicators is not None else "Failed"
                
                # Update savings data
                savings = self.fetch_savings_data(mkt)
                update_status[f"{mkt}_savings"] = "Updated" if savings is not None else "Failed"
            
            # Backup database after update
            self.backup_database()
            
            return update_status
        
        except Exception as e:
            self.logger.error(f"Error updating market data: {str(e)}")
            return {"status": "Failed", "error": str(e)}
    
    def create_portfolio(self, name, market, risk_profile):
        """
        CODEX: Create a new investment portfolio.
        
        Args:
            name (str): Portfolio name
            market (str): Target market (US, BR, or BOTH)
            risk_profile (str): Risk profile (conservative, moderate, aggressive)
        
        Returns:
            int: Portfolio ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert portfolio
            current_date = datetime.now().isoformat()
            cursor.execute('''
            INSERT INTO portfolios
            (name, market, risk_profile, created_date, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ''', (name, market, risk_profile, current_date, current_date))
            
            # Get portfolio ID
            portfolio_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return portfolio_id
        
        except Exception as e:
            self.logger.error(f"Error creating portfolio: {str(e)}")
            return None
    
    def add_asset_to_portfolio(self, portfolio_id, symbol, asset_type, allocation_percentage, purchase_price=None, purchase_date=None):
        """
        CODEX: Add an asset to a portfolio.
        
        Args:
            portfolio_id (int): Portfolio ID
            symbol (str): Asset symbol
            asset_type (str): Asset type (stock, bond, savings)
            allocation_percentage (float): Allocation percentage
            purchase_price (float, optional): Purchase price. Defaults to None.
            purchase_date (str, optional): Purchase date. Defaults to None.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert asset
            cursor.execute('''
            INSERT OR REPLACE INTO portfolio_assets
            (portfolio_id, symbol, asset_type, allocation_percentage, purchase_price, purchase_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (portfolio_id, symbol, asset_type, allocation_percentage, purchase_price, purchase_date))
            
            # Update portfolio last_updated
            cursor.execute('''
            UPDATE portfolios
            SET last_updated = ?
            WHERE id = ?
            ''', (datetime.now().isoformat(), portfolio_id))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error adding asset to portfolio: {str(e)}")
            return False
    
    def get_portfolio(self, portfolio_id=None, name=None):
        """
        CODEX: Get portfolio details.
        
        Args:
            portfolio_id (int, optional): Portfolio ID. Defaults to None.
            name (str, optional): Portfolio name. Defaults to None.
        
        Returns:
            dict: Portfolio details
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query portfolio
            if portfolio_id is not None:
                cursor.execute('''
                SELECT * FROM portfolios WHERE id = ?
                ''', (portfolio_id,))
            elif name is not None:
                cursor.execute('''
                SELECT * FROM portfolios WHERE name = ?
                ''', (name,))
            else:
                return None
            
            portfolio = cursor.fetchone()
            
            if portfolio is None:
                return None
            
            # Convert to dictionary
            portfolio_dict = {
                "id": portfolio[0],
                "name": portfolio[1],
                "market": portfolio[2],
                "risk_profile": portfolio[3],
                "created_date": portfolio[4],
                "last_updated": portfolio[5],
                "assets": []
            }
            
            # Query assets
            cursor.execute('''
            SELECT * FROM portfolio_assets WHERE portfolio_id = ?
            ''', (portfolio_dict["id"],))
            
            assets = cursor.fetchall()
            
            for asset in assets:
                asset_dict = {
                    "id": asset[0],
                    "portfolio_id": asset[1],
                    "symbol": asset[2],
                    "asset_type": asset[3],
                    "allocation_percentage": asset[4],
                    "purchase_price": asset[5],
                    "purchase_date": asset[6]
                }
                portfolio_dict["assets"].append(asset_dict)
            
            conn.close()
            
            return portfolio_dict
        
        except Exception as e:
            self.logger.error(f"Error retrieving portfolio: {str(e)}")
            return None
