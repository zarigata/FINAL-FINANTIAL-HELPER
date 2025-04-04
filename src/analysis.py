#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# ANALYSIS ENGINE MODULE v1.0
# CODEX: This module handles financial analysis and investment calculations.
# CODEX: Provides tools for market analysis, portfolio optimization, and investment planning.

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import json

class AnalysisEngine:
    """
    CODEX: Handles financial analysis and investment calculations.
    CODEX: Provides methods for analyzing market data and generating investment recommendations.
    """
    
    def __init__(self, config=None):
        """
        CODEX: Initialize the analysis engine.
        
        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Load default inflation rates
        self.inflation_rates = {
            "US": self.config.get("inflation", {}).get("us", 2.5),
            "BR": self.config.get("inflation", {}).get("brazil", 4.5)
        }
        
        # Load default risk profiles
        self.risk_profiles = self.config.get("risk_profiles", {
            "conservative": {"stocks": 20, "bonds": 60, "cash": 20},
            "moderate": {"stocks": 50, "bonds": 40, "cash": 10},
            "aggressive": {"stocks": 80, "bonds": 15, "cash": 5}
        })
    
    def analyze_stock(self, data, period="1y"):
        """
        CODEX: Analyze stock data.
        
        Args:
            data (pandas.DataFrame): Stock data
            period (str, optional): Analysis period. Defaults to "1y".
        
        Returns:
            dict: Analysis results
        """
        try:
            # Ensure data is sorted by date
            if 'Date' in data.columns:
                data = data.sort_values('Date')
            
            # Calculate basic metrics
            start_price = data['Close'].iloc[0]
            end_price = data['Close'].iloc[-1]
            price_change = end_price - start_price
            price_change_pct = (price_change / start_price) * 100
            
            # Calculate returns
            daily_returns = data['Close'].pct_change().dropna()
            
            # Calculate volatility (annualized)
            volatility = daily_returns.std() * np.sqrt(252) * 100
            
            # Calculate Sharpe ratio (assuming risk-free rate of 2%)
            risk_free_rate = 0.02
            sharpe_ratio = (daily_returns.mean() * 252 - risk_free_rate) / (daily_returns.std() * np.sqrt(252))
            
            # Calculate moving averages
            data['MA50'] = data['Close'].rolling(window=50).mean()
            data['MA200'] = data['Close'].rolling(window=200).mean()
            
            # Determine trend
            if data['MA50'].iloc[-1] > data['MA200'].iloc[-1]:
                trend = "Bullish"
            else:
                trend = "Bearish"
            
            # Calculate RSI (Relative Strength Index)
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # Determine if overbought or oversold
            rsi = data['RSI'].iloc[-1]
            if rsi > 70:
                rsi_signal = "Overbought"
            elif rsi < 30:
                rsi_signal = "Oversold"
            else:
                rsi_signal = "Neutral"
            
            # Prepare result
            result = {
                "symbol": data['symbol'].iloc[0] if 'symbol' in data.columns else "Unknown",
                "start_date": data['Date'].iloc[0] if 'Date' in data.columns else "Unknown",
                "end_date": data['Date'].iloc[-1] if 'Date' in data.columns else "Unknown",
                "start_price": start_price,
                "end_price": end_price,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "trend": trend,
                "rsi": rsi,
                "rsi_signal": rsi_signal,
                "highest_price": data['High'].max(),
                "lowest_price": data['Low'].min(),
                "average_volume": data['Volume'].mean() if 'Volume' in data.columns else 0
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error analyzing stock: {str(e)}")
            return {"error": str(e)}
    
    def forecast_stock_price(self, data, days=30):
        """
        CODEX: Forecast stock price using ARIMA model.
        
        Args:
            data (pandas.DataFrame): Historical stock data
            days (int, optional): Number of days to forecast. Defaults to 30.
        
        Returns:
            dict: Forecast results
        """
        try:
            # Ensure data is sorted by date
            if 'Date' in data.columns:
                data = data.sort_values('Date')
            
            # Extract closing prices
            prices = data['Close'].values
            
            # Check if data is stationary
            result = adfuller(prices)
            if result[1] > 0.05:
                # Data is not stationary, take first difference
                prices = np.diff(prices)
            
            # Fit ARIMA model
            model = ARIMA(prices, order=(5, 1, 0))
            model_fit = model.fit()
            
            # Forecast future prices
            forecast = model_fit.forecast(steps=days)
            
            # If we differenced the data, we need to integrate to get actual prices
            if result[1] > 0.05:
                last_price = data['Close'].iloc[-1]
                forecast = np.cumsum(forecast) + last_price
            
            # Calculate confidence intervals
            confidence = 0.95
            forecast_std = np.std(forecast)
            z_value = stats.norm.ppf((1 + confidence) / 2)
            lower_bound = forecast - z_value * forecast_std
            upper_bound = forecast + z_value * forecast_std
            
            # Prepare dates for forecast
            last_date = data['Date'].iloc[-1] if 'Date' in data.columns else datetime.now()
            if isinstance(last_date, str):
                last_date = datetime.fromisoformat(last_date)
            
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(days)]
            forecast_dates = [date.isoformat() for date in forecast_dates]
            
            # Prepare result
            result = {
                "symbol": data['symbol'].iloc[0] if 'symbol' in data.columns else "Unknown",
                "last_price": data['Close'].iloc[-1],
                "forecast_start_date": forecast_dates[0],
                "forecast_end_date": forecast_dates[-1],
                "forecast_days": days,
                "forecast_prices": forecast.tolist(),
                "lower_bound": lower_bound.tolist(),
                "upper_bound": upper_bound.tolist(),
                "forecast_dates": forecast_dates
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error forecasting stock price: {str(e)}")
            return {"error": str(e)}
    
    def calculate_investment_growth(self, initial_amount, annual_return, years, inflation_rate=None, market="US", compound_frequency=1):
        """
        CODEX: Calculate investment growth over time.
        
        Args:
            initial_amount (float): Initial investment amount
            annual_return (float): Annual return rate (as decimal)
            years (int): Investment timeline in years
            inflation_rate (float, optional): Inflation rate (as decimal). Defaults to None.
            market (str, optional): Market (US or BR). Defaults to "US".
            compound_frequency (int, optional): Compounding frequency per year. Defaults to 1.
        
        Returns:
            dict: Investment growth results
        """
        try:
            # Use provided inflation rate or default for the market
            if inflation_rate is None:
                inflation_rate = self.inflation_rates.get(market, 2.5) / 100
            
            # Calculate nominal growth
            periods = years * compound_frequency
            rate_per_period = annual_return / compound_frequency
            
            nominal_value = initial_amount * (1 + rate_per_period) ** periods
            nominal_growth = nominal_value - initial_amount
            
            # Calculate real (inflation-adjusted) growth
            real_rate_per_period = (1 + rate_per_period) / (1 + inflation_rate / compound_frequency) - 1
            real_value = initial_amount * (1 + real_rate_per_period) ** periods
            real_growth = real_value - initial_amount
            
            # Generate year-by-year growth
            yearly_growth = []
            for year in range(years + 1):
                periods_completed = year * compound_frequency
                nominal_value_at_year = initial_amount * (1 + rate_per_period) ** periods_completed
                real_value_at_year = initial_amount * (1 + real_rate_per_period) ** periods_completed
                
                yearly_growth.append({
                    "year": year,
                    "nominal_value": nominal_value_at_year,
                    "real_value": real_value_at_year
                })
            
            # Prepare result
            result = {
                "initial_amount": initial_amount,
                "annual_return": annual_return * 100,  # Convert to percentage
                "years": years,
                "inflation_rate": inflation_rate * 100,  # Convert to percentage
                "compound_frequency": compound_frequency,
                "final_nominal_value": nominal_value,
                "nominal_growth": nominal_growth,
                "nominal_growth_pct": (nominal_growth / initial_amount) * 100,
                "final_real_value": real_value,
                "real_growth": real_growth,
                "real_growth_pct": (real_growth / initial_amount) * 100,
                "yearly_growth": yearly_growth
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error calculating investment growth: {str(e)}")
            return {"error": str(e)}
    
    def calculate_goal_based_investment(self, goal_amount, years, inflation_rate=None, market="US", risk_profile="moderate"):
        """
        CODEX: Calculate required investment to reach a financial goal.
        
        Args:
            goal_amount (float): Target amount to reach
            years (int): Investment timeline in years
            inflation_rate (float, optional): Inflation rate (as decimal). Defaults to None.
            market (str, optional): Market (US or BR). Defaults to "US".
            risk_profile (str, optional): Risk profile. Defaults to "moderate".
        
        Returns:
            dict: Goal-based investment results
        """
        try:
            # Use provided inflation rate or default for the market
            if inflation_rate is None:
                inflation_rate = self.inflation_rates.get(market, 2.5) / 100
            
            # Adjust goal amount for inflation
            inflation_adjusted_goal = goal_amount * (1 + inflation_rate) ** years
            
            # Estimate returns based on risk profile
            estimated_returns = self._estimate_returns_by_risk_profile(risk_profile, market)
            
            # Calculate required monthly investment
            monthly_rate = estimated_returns['combined'] / 12
            months = years * 12
            
            # Formula: PMT = FV * r / ((1 + r)^n - 1)
            # Where PMT is monthly payment, FV is future value, r is monthly rate, n is number of months
            monthly_investment = inflation_adjusted_goal * monthly_rate / ((1 + monthly_rate) ** months - 1)
            
            # Calculate lump sum investment
            lump_sum_investment = inflation_adjusted_goal / (1 + estimated_returns['combined']) ** years
            
            # Generate year-by-year projection for monthly investment
            monthly_projection = []
            accumulated = 0
            
            for year in range(years + 1):
                months_completed = year * 12
                if year == 0:
                    value = 0
                else:
                    value = monthly_investment * ((1 + monthly_rate) ** months_completed - 1) / monthly_rate
                
                monthly_projection.append({
                    "year": year,
                    "value": value,
                    "inflation_adjusted_value": value / (1 + inflation_rate) ** year
                })
            
            # Generate year-by-year projection for lump sum investment
            lump_sum_projection = []
            
            for year in range(years + 1):
                value = lump_sum_investment * (1 + estimated_returns['combined']) ** year
                
                lump_sum_projection.append({
                    "year": year,
                    "value": value,
                    "inflation_adjusted_value": value / (1 + inflation_rate) ** year
                })
            
            # Prepare result
            result = {
                "goal_amount": goal_amount,
                "years": years,
                "inflation_rate": inflation_rate * 100,  # Convert to percentage
                "inflation_adjusted_goal": inflation_adjusted_goal,
                "risk_profile": risk_profile,
                "estimated_returns": {
                    "stocks": estimated_returns['stocks'] * 100,  # Convert to percentage
                    "bonds": estimated_returns['bonds'] * 100,  # Convert to percentage
                    "cash": estimated_returns['cash'] * 100,  # Convert to percentage
                    "combined": estimated_returns['combined'] * 100  # Convert to percentage
                },
                "monthly_investment": monthly_investment,
                "annual_investment": monthly_investment * 12,
                "lump_sum_investment": lump_sum_investment,
                "monthly_projection": monthly_projection,
                "lump_sum_projection": lump_sum_projection
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error calculating goal-based investment: {str(e)}")
            return {"error": str(e)}
    
    def _estimate_returns_by_risk_profile(self, risk_profile, market="US"):
        """
        CODEX: Estimate returns based on risk profile and market.
        
        Args:
            risk_profile (str): Risk profile (conservative, moderate, aggressive)
            market (str, optional): Market (US or BR). Defaults to "US".
        
        Returns:
            dict: Estimated returns for different asset classes
        """
        # Base returns for US market
        base_returns = {
            "stocks": 0.10,  # 10% annual return for stocks
            "bonds": 0.04,   # 4% annual return for bonds
            "cash": 0.02     # 2% annual return for cash/savings
        }
        
        # Adjust returns for Brazilian market
        if market == "BR":
            base_returns = {
                "stocks": 0.12,  # 12% annual return for stocks
                "bonds": 0.08,   # 8% annual return for bonds
                "cash": 0.06     # 6% annual return for cash/savings
            }
        
        # Get allocation based on risk profile
        allocation = self.risk_profiles.get(risk_profile, self.risk_profiles["moderate"])
        
        # Calculate combined return based on allocation
        combined_return = (
            base_returns["stocks"] * allocation["stocks"] / 100 +
            base_returns["bonds"] * allocation["bonds"] / 100 +
            base_returns["cash"] * allocation["cash"] / 100
        )
        
        return {
            "stocks": base_returns["stocks"],
            "bonds": base_returns["bonds"],
            "cash": base_returns["cash"],
            "combined": combined_return
        }
    
    def optimize_portfolio(self, assets_data, risk_tolerance=0.5):
        """
        CODEX: Optimize portfolio allocation using Modern Portfolio Theory.
        
        Args:
            assets_data (dict): Dictionary of assets data (symbol -> returns)
            risk_tolerance (float, optional): Risk tolerance (0-1). Defaults to 0.5.
        
        Returns:
            dict: Optimized portfolio allocation
        """
        try:
            # This is a simplified implementation of portfolio optimization
            # In a real implementation, this would use more sophisticated methods
            
            # Extract returns and calculate statistics
            returns = pd.DataFrame(assets_data)
            
            # Calculate expected returns (mean of historical returns)
            expected_returns = returns.mean()
            
            # Calculate covariance matrix
            cov_matrix = returns.cov()
            
            # Generate random portfolios
            num_portfolios = 10000
            results = np.zeros((3, num_portfolios))
            weights_record = []
            
            for i in range(num_portfolios):
                # Generate random weights
                weights = np.random.random(len(assets_data))
                weights /= np.sum(weights)
                weights_record.append(weights)
                
                # Calculate portfolio return and volatility
                portfolio_return = np.sum(expected_returns * weights)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                
                # Calculate Sharpe ratio (assuming risk-free rate of 2%)
                sharpe_ratio = (portfolio_return - 0.02) / portfolio_volatility
                
                # Store results
                results[0, i] = portfolio_return
                results[1, i] = portfolio_volatility
                results[2, i] = sharpe_ratio
            
            # Convert results to DataFrame
            results_df = pd.DataFrame(results.T, columns=['Return', 'Volatility', 'Sharpe'])
            
            # Find portfolio with highest Sharpe ratio
            max_sharpe_idx = results_df['Sharpe'].idxmax()
            max_sharpe_weights = weights_record[max_sharpe_idx]
            
            # Find portfolio with minimum volatility
            min_vol_idx = results_df['Volatility'].idxmin()
            min_vol_weights = weights_record[min_vol_idx]
            
            # Find portfolio based on risk tolerance
            # Higher risk tolerance -> closer to max Sharpe portfolio
            # Lower risk tolerance -> closer to min volatility portfolio
            optimal_weights = risk_tolerance * np.array(max_sharpe_weights) + (1 - risk_tolerance) * np.array(min_vol_weights)
            
            # Normalize weights to ensure they sum to 1
            optimal_weights = optimal_weights / np.sum(optimal_weights)
            
            # Prepare result
            symbols = list(assets_data.keys())
            allocation = {}
            
            for i, symbol in enumerate(symbols):
                allocation[symbol] = optimal_weights[i] * 100  # Convert to percentage
            
            # Calculate expected portfolio statistics
            expected_return = np.sum(expected_returns * optimal_weights) * 100  # Convert to percentage
            expected_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights))) * 100  # Convert to percentage
            
            result = {
                "allocation": allocation,
                "expected_annual_return": expected_return,
                "expected_annual_volatility": expected_volatility,
                "sharpe_ratio": (expected_return / 100 - 0.02) / (expected_volatility / 100)
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error optimizing portfolio: {str(e)}")
            return {"error": str(e)}
    
    def compare_investments(self, investments, years, initial_amount=1000):
        """
        CODEX: Compare different investment options.
        
        Args:
            investments (list): List of investment options with returns
            years (int): Investment timeline in years
            initial_amount (float, optional): Initial investment amount. Defaults to 1000.
        
        Returns:
            dict: Comparison results
        """
        try:
            # Calculate growth for each investment
            comparison = {}
            
            for investment in investments:
                name = investment.get("name", "Unknown")
                annual_return = investment.get("annual_return", 0) / 100  # Convert from percentage
                inflation_rate = investment.get("inflation_rate", 0) / 100  # Convert from percentage
                
                # Calculate growth
                growth = self.calculate_investment_growth(
                    initial_amount=initial_amount,
                    annual_return=annual_return,
                    years=years,
                    inflation_rate=inflation_rate
                )
                
                comparison[name] = {
                    "initial_amount": initial_amount,
                    "annual_return": annual_return * 100,  # Convert to percentage
                    "final_nominal_value": growth["final_nominal_value"],
                    "final_real_value": growth["final_real_value"],
                    "nominal_growth_pct": growth["nominal_growth_pct"],
                    "real_growth_pct": growth["real_growth_pct"],
                    "yearly_growth": growth["yearly_growth"]
                }
            
            # Rank investments by final real value
            rankings = sorted(
                comparison.keys(),
                key=lambda x: comparison[x]["final_real_value"],
                reverse=True
            )
            
            result = {
                "initial_amount": initial_amount,
                "years": years,
                "investments": comparison,
                "rankings": rankings
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error comparing investments: {str(e)}")
            return {"error": str(e)}
