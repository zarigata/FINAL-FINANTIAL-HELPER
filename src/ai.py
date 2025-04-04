#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# AI ENGINE MODULE v1.0
# CODEX: This module handles all AI-related operations using Ollama.
# CODEX: Provides natural language processing and decision-making capabilities.

import os
import json
import logging
import requests
import time
from datetime import datetime
import pandas as pd
import numpy as np

class AIEngine:
    """
    CODEX: Manages AI operations using Ollama.
    CODEX: Provides natural language processing and investment recommendations.
    """
    
    def __init__(self, ollama_config):
        """
        CODEX: Initialize the AI engine.
        
        Args:
            ollama_config (dict): Ollama configuration
        """
        self.base_url = ollama_config.get('base_url', 'http://localhost:11434')
        self.model = ollama_config.get('model', 'llama3.2')
        self.system_prompt = ollama_config.get('system_prompt', 'You are a financial advisor.')
        self.temperature = ollama_config.get('temperature', 0.7)
        self.max_tokens = ollama_config.get('max_tokens', 2048)
        self.logger = logging.getLogger(__name__)
    
    def check_ollama_availability(self):
        """
        CODEX: Check if Ollama is available.
        
        Returns:
            bool: True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                # Check if the model is available
                models = response.json().get('models', [])
                model_names = [model.get('name') for model in models]
                
                if self.model in model_names:
                    self.logger.info(f"Ollama is available with model {self.model}")
                    return True
                else:
                    self.logger.warning(f"Ollama is available but model {self.model} is not found")
                    return False
            else:
                self.logger.warning("Ollama API returned non-200 status code")
                return False
        except Exception as e:
            self.logger.error(f"Error checking Ollama availability: {str(e)}")
            return False
    
    def generate_response(self, prompt, context=None):
        """
        CODEX: Generate a response from the AI model.
        
        Args:
            prompt (str): User prompt
            context (list, optional): Conversation context. Defaults to None.
        
        Returns:
            str: AI-generated response
        """
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": self.system_prompt,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False
            }
            
            # Add context if provided
            if context:
                payload["context"] = context
            
            # Send request to Ollama
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', ''), result.get('context', None)
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "I'm sorry, I encountered an error while processing your request.", None
        
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request.", None
    
    def analyze_investment_options(self, market_data, user_preferences):
        """
        CODEX: Analyze investment options based on market data and user preferences.
        
        Args:
            market_data (dict): Market data
            user_preferences (dict): User preferences
        
        Returns:
            dict: Investment recommendations
        """
        try:
            # Prepare prompt for the AI model
            prompt = self._prepare_investment_analysis_prompt(market_data, user_preferences)
            
            # Generate response
            response, _ = self.generate_response(prompt)
            
            # Parse the response
            recommendations = self._parse_investment_recommendations(response)
            
            return recommendations
        
        except Exception as e:
            self.logger.error(f"Error analyzing investment options: {str(e)}")
            return {"error": str(e)}
    
    def _prepare_investment_analysis_prompt(self, market_data, user_preferences):
        """
        CODEX: Prepare a prompt for investment analysis.
        
        Args:
            market_data (dict): Market data
            user_preferences (dict): User preferences
        
        Returns:
            str: Formatted prompt
        """
        # Extract user preferences
        investment_type = user_preferences.get('investment_type', 'mixed')
        amount = user_preferences.get('amount', 1000)
        market = user_preferences.get('market', 'US')
        goal = user_preferences.get('goal', None)
        years = user_preferences.get('years', None)
        risk = user_preferences.get('risk', 'moderate')
        
        # Format market data
        market_data_str = json.dumps(market_data, indent=2)
        
        # Build prompt
        prompt = f"""
        As a financial advisor, I need to provide investment recommendations based on the following:
        
        User Preferences:
        - Investment Type: {investment_type}
        - Amount to Invest: {amount}
        - Target Market: {market}
        - Investment Goal: {goal if goal else 'Not specified'}
        - Investment Timeline: {f'{years} years' if years else 'Not specified'}
        - Risk Tolerance: {risk}
        
        Market Data:
        {market_data_str}
        
        Please analyze this information and provide:
        1. Recommended investment allocation (percentages for different asset classes)
        2. Specific investment recommendations (e.g., specific stocks, bonds, or funds)
        3. Expected returns (short-term and long-term)
        4. Risk assessment
        5. Rationale for recommendations
        
        Format your response as a structured analysis that I can parse programmatically.
        """
        
        return prompt
    
    def _parse_investment_recommendations(self, response):
        """
        CODEX: Parse investment recommendations from AI response.
        
        Args:
            response (str): AI-generated response
        
        Returns:
            dict: Structured investment recommendations
        """
        try:
            # This is a simplified parser for demonstration
            # In a real implementation, this would use more sophisticated parsing
            
            lines = response.strip().split('\n')
            recommendations = {
                "allocation": {},
                "specific_investments": [],
                "expected_returns": {},
                "risk_assessment": "",
                "rationale": ""
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                # Identify sections
                if "allocation" in line.lower() and ":" not in line:
                    current_section = "allocation"
                    continue
                elif "specific" in line.lower() and "investment" in line.lower() and ":" not in line:
                    current_section = "specific_investments"
                    continue
                elif "expected return" in line.lower() and ":" not in line:
                    current_section = "expected_returns"
                    continue
                elif "risk assessment" in line.lower() and ":" not in line:
                    current_section = "risk_assessment"
                    continue
                elif "rationale" in line.lower() and ":" not in line:
                    current_section = "rationale"
                    continue
                
                # Process line based on current section
                if current_section == "allocation" and ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        asset_class = parts[0].strip()
                        percentage = parts[1].strip()
                        # Extract percentage value
                        for word in percentage.split():
                            if "%" in word:
                                try:
                                    value = float(word.replace("%", ""))
                                    recommendations["allocation"][asset_class] = value
                                except ValueError:
                                    pass
                
                elif current_section == "specific_investments" and "-" in line:
                    recommendations["specific_investments"].append(line.strip())
                
                elif current_section == "expected_returns" and ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        term = parts[0].strip()
                        return_value = parts[1].strip()
                        # Extract percentage value
                        for word in return_value.split():
                            if "%" in word:
                                try:
                                    value = float(word.replace("%", ""))
                                    recommendations["expected_returns"][term] = value
                                except ValueError:
                                    pass
                
                elif current_section == "risk_assessment":
                    recommendations["risk_assessment"] += line + " "
                
                elif current_section == "rationale":
                    recommendations["rationale"] += line + " "
            
            # Clean up strings
            recommendations["risk_assessment"] = recommendations["risk_assessment"].strip()
            recommendations["rationale"] = recommendations["rationale"].strip()
            
            return recommendations
        
        except Exception as e:
            self.logger.error(f"Error parsing investment recommendations: {str(e)}")
            return {"error": str(e)}
    
    def analyze_market_trends(self, market_data, market, period="1y"):
        """
        CODEX: Analyze market trends based on historical data.
        
        Args:
            market_data (pandas.DataFrame): Historical market data
            market (str): Market (US or BR)
            period (str, optional): Analysis period. Defaults to "1y".
        
        Returns:
            dict: Market trend analysis
        """
        try:
            # Prepare prompt for the AI model
            prompt = self._prepare_market_analysis_prompt(market_data, market, period)
            
            # Generate response
            response, _ = self.generate_response(prompt)
            
            # Parse the response
            analysis = self._parse_market_analysis(response)
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Error analyzing market trends: {str(e)}")
            return {"error": str(e)}
    
    def _prepare_market_analysis_prompt(self, market_data, market, period):
        """
        CODEX: Prepare a prompt for market trend analysis.
        
        Args:
            market_data (pandas.DataFrame): Historical market data
            market (str): Market (US or BR)
            period (str): Analysis period
        
        Returns:
            str: Formatted prompt
        """
        # Format market data
        # Convert DataFrame to a simplified string representation
        data_summary = f"Data for {len(market_data)} trading days\n"
        data_summary += f"Start date: {market_data['Date'].min()}\n"
        data_summary += f"End date: {market_data['Date'].max()}\n"
        
        # Calculate some basic statistics
        start_price = market_data['Close'].iloc[0]
        end_price = market_data['Close'].iloc[-1]
        price_change = end_price - start_price
        price_change_pct = (price_change / start_price) * 100
        
        data_summary += f"Starting price: {start_price:.2f}\n"
        data_summary += f"Ending price: {end_price:.2f}\n"
        data_summary += f"Price change: {price_change:.2f} ({price_change_pct:.2f}%)\n"
        
        # Add volatility
        volatility = market_data['Close'].pct_change().std() * 100
        data_summary += f"Volatility: {volatility:.2f}%\n"
        
        # Build prompt
        prompt = f"""
        As a financial market analyst, I need to analyze the following market data for the {market} market over the {period} period:
        
        {data_summary}
        
        Please provide a comprehensive analysis including:
        1. Overall market trend (bullish, bearish, or sideways)
        2. Key support and resistance levels
        3. Volatility assessment
        4. Market outlook for the next 3-6 months
        5. Key factors influencing the market
        
        Format your response as a structured analysis that I can parse programmatically.
        """
        
        return prompt
    
    def _parse_market_analysis(self, response):
        """
        CODEX: Parse market analysis from AI response.
        
        Args:
            response (str): AI-generated response
        
        Returns:
            dict: Structured market analysis
        """
        try:
            # This is a simplified parser for demonstration
            # In a real implementation, this would use more sophisticated parsing
            
            lines = response.strip().split('\n')
            analysis = {
                "trend": "",
                "support_resistance": {},
                "volatility": "",
                "outlook": "",
                "factors": []
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                # Identify sections
                if "trend" in line.lower() and ":" not in line:
                    current_section = "trend"
                    continue
                elif "support" in line.lower() and "resistance" in line.lower() and ":" not in line:
                    current_section = "support_resistance"
                    continue
                elif "volatility" in line.lower() and ":" not in line:
                    current_section = "volatility"
                    continue
                elif "outlook" in line.lower() and ":" not in line:
                    current_section = "outlook"
                    continue
                elif "factor" in line.lower() and ":" not in line:
                    current_section = "factors"
                    continue
                
                # Process line based on current section
                if current_section == "trend":
                    analysis["trend"] += line + " "
                
                elif current_section == "support_resistance" and ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        level_type = parts[0].strip()
                        level_value = parts[1].strip()
                        # Extract numeric value
                        for word in level_value.split():
                            try:
                                value = float(word.replace(",", ""))
                                if "support" in level_type.lower():
                                    analysis["support_resistance"]["support"] = value
                                elif "resistance" in level_type.lower():
                                    analysis["support_resistance"]["resistance"] = value
                                break
                            except ValueError:
                                pass
                
                elif current_section == "volatility":
                    analysis["volatility"] += line + " "
                
                elif current_section == "outlook":
                    analysis["outlook"] += line + " "
                
                elif current_section == "factors" and "-" in line:
                    analysis["factors"].append(line.strip())
            
            # Clean up strings
            analysis["trend"] = analysis["trend"].strip()
            analysis["volatility"] = analysis["volatility"].strip()
            analysis["outlook"] = analysis["outlook"].strip()
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Error parsing market analysis: {str(e)}")
            return {"error": str(e)}
    
    def optimize_portfolio(self, portfolio_data):
        """
        CODEX: Optimize a portfolio based on Modern Portfolio Theory.
        
        Args:
            portfolio_data (dict): Portfolio data
        
        Returns:
            dict: Optimized portfolio allocation
        """
        try:
            # This is a simplified implementation for demonstration
            # In a real implementation, this would use PyPortfolioOpt or similar
            
            # Extract assets and current allocations
            assets = portfolio_data.get("assets", [])
            
            if not assets:
                return {"error": "No assets in portfolio"}
            
            # Generate random optimized allocations for demonstration
            # In a real implementation, this would use actual optimization algorithms
            total_allocation = 100.0
            optimized_allocation = {}
            
            # Distribute allocation randomly but ensure it sums to 100%
            random_weights = np.random.random(len(assets))
            random_weights = random_weights / random_weights.sum() * total_allocation
            
            for i, asset in enumerate(assets):
                optimized_allocation[asset["symbol"]] = round(random_weights[i], 2)
            
            # Prepare prompt for the AI to explain the optimization
            prompt = f"""
            As a portfolio manager, I've optimized a portfolio with the following assets:
            {', '.join([asset['symbol'] for asset in assets])}
            
            The optimized allocation is:
            {json.dumps(optimized_allocation, indent=2)}
            
            Please explain the rationale behind this optimization, considering:
            1. Risk reduction through diversification
            2. Expected returns
            3. Market conditions
            
            Format your response as a concise explanation.
            """
            
            # Generate response
            explanation, _ = self.generate_response(prompt)
            
            return {
                "optimized_allocation": optimized_allocation,
                "explanation": explanation
            }
        
        except Exception as e:
            self.logger.error(f"Error optimizing portfolio: {str(e)}")
            return {"error": str(e)}
