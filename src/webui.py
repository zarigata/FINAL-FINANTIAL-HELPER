#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# WEBUI MODULE v1.0
# CODEX: This module provides a web-based user interface for testing FinBot functionality.
# CODEX: It allows users to interact with all components of the application through a browser.

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Flask imports
from flask import Flask, render_template, request, jsonify, redirect, url_for
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

# Add project directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import internal modules
from src.config import ConfigManager
from src.data import DataManager
from src.analysis import AnalysisEngine
from src.ai import AIEngine
from src.utils import setup_logging

# Try to import API integrations
try:
    from src.api_integrations.alpha_vantage import AlphaVantageAPI
    from src.api_integrations.b3_api import B3API
    alpha_vantage_available = True
    b3_api_available = True
except ImportError:
    alpha_vantage_available = False
    b3_api_available = False
    logging.warning("API integration modules not available")

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"))

# Initialize components
config_manager = None
data_manager = None
analysis_engine = None
ai_engine = None
alpha_vantage_api = None
b3_api = None

# Setup logging
logger = logging.getLogger(__name__)

def initialize_components():
    """
    CODEX: Initialize all components of the FinBot application.
    CODEX: This ensures that all modules are properly loaded before use.
    """
    global config_manager, data_manager, analysis_engine, ai_engine, alpha_vantage_api, b3_api
    
    try:
        # Initialize config manager
        config_manager = ConfigManager()
        
        # Initialize data manager
        data_manager = DataManager(config_manager)
        
        # Initialize analysis engine
        analysis_engine = AnalysisEngine(config_manager, data_manager)
        
        # Initialize AI engine
        ai_engine = AIEngine(config_manager)
        
        # Initialize API clients if available
        if alpha_vantage_available:
            alpha_vantage_api = AlphaVantageAPI(
                api_key=config_manager.get_config("data_sources.alpha_vantage.api_key", "")
            )
        
        if b3_api_available:
            b3_api = B3API()
        
        logger.info("All components initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        return False

@app.route('/')
def index():
    """
    CODEX: Render the main dashboard page.
    """
    return render_template('index.html', 
                          alpha_vantage_available=alpha_vantage_available,
                          b3_api_available=b3_api_available)

@app.route('/invest', methods=['GET', 'POST'])
def invest():
    """
    CODEX: Handle investment planning requests.
    """
    if request.method == 'POST':
        # Get form data
        amount = float(request.form.get('amount', 1000))
        market = request.form.get('market', 'US')
        investment_type = request.form.get('type', 'stocks')
        goal = float(request.form.get('goal', 0)) if request.form.get('goal') else None
        years = int(request.form.get('years', 10)) if request.form.get('years') else None
        risk_tolerance = request.form.get('risk_tolerance', 'moderate')
        
        try:
            # Get investment recommendations
            if analysis_engine:
                result = analysis_engine.get_investment_recommendations(
                    amount=amount,
                    market=market,
                    investment_type=investment_type,
                    goal=goal,
                    years=years,
                    risk_tolerance=risk_tolerance
                )
                
                # Generate chart if data is available
                chart_json = None
                if result and 'projected_growth' in result:
                    fig = px.line(
                        x=list(range(years + 1)),
                        y=result['projected_growth'],
                        labels={'x': 'Years', 'y': 'Value'},
                        title=f'Projected Growth over {years} Years'
                    )
                    chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
                
                return render_template(
                    'invest_result.html',
                    result=result,
                    chart_json=chart_json,
                    amount=amount,
                    market=market,
                    investment_type=investment_type,
                    goal=goal,
                    years=years,
                    risk_tolerance=risk_tolerance
                )
            else:
                return render_template(
                    'error.html',
                    error="Analysis engine not initialized"
                )
        
        except Exception as e:
            logger.error(f"Error processing investment request: {str(e)}")
            return render_template('error.html', error=str(e))
    
    # GET request - show form
    return render_template('invest.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """
    CODEX: Handle market analysis requests.
    """
    if request.method == 'POST':
        # Get form data
        symbol = request.form.get('symbol', '')
        market = request.form.get('market', 'US')
        period = request.form.get('period', '1y')
        
        try:
            # Get market analysis
            if analysis_engine:
                result = analysis_engine.analyze_market(
                    symbol=symbol,
                    market=market,
                    period=period
                )
                
                # Generate chart if data is available
                chart_json = None
                if result and 'historical_data' in result:
                    df = result['historical_data']
                    fig = go.Figure(data=[go.Candlestick(
                        x=df['Date'],
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close']
                    )])
                    fig.update_layout(title=f'{symbol} Price History')
                    chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
                
                # Get news related to the symbol
                news_items = []
                try:
                    if hasattr(analysis_engine, 'get_news'):
                        news_items = analysis_engine.get_news(symbol=symbol, market=market, limit=3)
                except Exception as e:
                    logger.warning(f"Error fetching news for {symbol}: {str(e)}")
                
                return render_template(
                    'analyze_result.html',
                    symbol=symbol,
                    market=market,
                    period=period,
                    result=result,
                    chart_json=chart_json,
                    news=news_items,
                    now=datetime.now
                )
            else:
                return render_template(
                    'error.html',
                    error="Analysis engine not initialized"
                )
        
        except Exception as e:
            logger.error(f"Error processing analysis request: {str(e)}")
            return render_template('error.html', error=str(e))
    
    # GET request - show form
    return render_template('analyze.html')

@app.route('/trends', methods=['GET', 'POST'])
def trends():
    """
    CODEX: Handle market trend analysis requests.
    """
    if request.method == 'POST':
        # Get form data
        market = request.form.get('market', 'US')
        asset_type = request.form.get('type', 'stocks')
        period = request.form.get('period', '1y')
        
        try:
            # Get trend analysis
            if analysis_engine and ai_engine:
                # Get market data
                market_data = data_manager.get_market_data(
                    market=market,
                    asset_type=asset_type,
                    period=period
                )
                
                # Analyze trends
                result = analysis_engine.analyze_trends(
                    market_data=market_data,
                    market=market,
                    asset_type=asset_type,
                    period=period
                )
                
                # Get AI insights
                ai_insights = ai_engine.get_market_insights(
                    market=market,
                    asset_type=asset_type,
                    period=period,
                    trend_data=result
                )
                
                # Generate chart if data is available
                chart_json = None
                if result and 'forecast' in result:
                    # Combine historical and forecast data
                    historical = result.get('historical', [])
                    forecast = result.get('forecast', [])
                    
                    # Create figure with two traces
                    fig = go.Figure()
                    
                    # Add historical data
                    fig.add_trace(go.Scatter(
                        x=list(range(len(historical))),
                        y=historical,
                        mode='lines',
                        name='Historical'
                    ))
                    
                    # Add forecast data
                    fig.add_trace(go.Scatter(
                        x=list(range(len(historical) - 1, len(historical) + len(forecast))),
                        y=forecast,
                        mode='lines',
                        name='Forecast',
                        line=dict(dash='dash')
                    ))
                    
                    fig.update_layout(title=f'{market} {asset_type} Trend Analysis')
                    chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
                
                return render_template(
                    'trends_result.html',
                    result=result,
                    ai_insights=ai_insights,
                    chart_json=chart_json,
                    market=market,
                    asset_type=asset_type,
                    period=period
                )
            else:
                return render_template(
                    'error.html',
                    error="Analysis engine or AI engine not initialized"
                )
        
        except Exception as e:
            logger.error(f"Error processing trend analysis request: {str(e)}")
            return render_template('error.html', error=str(e))
    
    # GET request - show form
    return render_template('trends.html')

@app.route('/news', methods=['GET', 'POST'])
def news():
    """
    CODEX: Handle news fetching and analysis requests.
    """
    if request.method == 'POST':
        # Get form data
        source = request.form.get('source', 'infomoney')
        market = request.form.get('market', 'BR')
        symbol = request.form.get('symbol', '')
        limit = int(request.form.get('limit', 10))
        
        try:
            # Check if web_scraper module is available
            web_scraper_available = False
            try:
                from src.web_scraper import WebScraper
                web_scraper = WebScraper()
                web_scraper_available = True
            except ImportError:
                logger.warning("Web scraper module not available")
            
            if web_scraper_available:
                # Fetch news
                news_items = web_scraper.scrape_news(
                    source=source,
                    limit=limit
                )
                
                # Analyze news sentiment if symbol is provided
                sentiment = None
                if symbol and ai_engine:
                    sentiment = web_scraper.analyze_news_sentiment(
                        symbol=symbol,
                        market=market
                    )
                
                return render_template(
                    'news_result.html',
                    news_items=news_items,
                    sentiment=sentiment,
                    source=source,
                    market=market,
                    symbol=symbol
                )
            else:
                # Mock news data for testing
                news_items = [
                    {
                        'title': 'Market shows strong recovery',
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'summary': 'The market showed strong recovery after recent volatility.',
                        'url': '#'
                    },
                    {
                        'title': 'Central Bank announces new interest rates',
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'summary': 'The Central Bank announced new interest rates today.',
                        'url': '#'
                    }
                ]
                
                return render_template(
                    'news_result.html',
                    news_items=news_items,
                    sentiment=None,
                    source=source,
                    market=market,
                    symbol=symbol,
                    mock_data=True
                )
        
        except Exception as e:
            logger.error(f"Error processing news request: {str(e)}")
            return render_template('error.html', error=str(e))
    
    # GET request - show form
    return render_template('news.html')

@app.route('/update-data', methods=['GET', 'POST'])
def update_data():
    """
    CODEX: Handle data update requests.
    """
    if request.method == 'POST':
        # Get form data
        market = request.form.get('market', 'US')
        asset_type = request.form.get('type', 'stocks')
        symbols = request.form.get('symbols', '').split(',')
        symbols = [s.strip() for s in symbols if s.strip()]
        
        try:
            # Update data
            if data_manager:
                result = data_manager.update_market_data(
                    market=market,
                    asset_type=asset_type,
                    symbols=symbols
                )
                
                return render_template(
                    'update_data_result.html',
                    result=result,
                    market=market,
                    asset_type=asset_type,
                    symbols=symbols
                )
            else:
                return render_template(
                    'error.html',
                    error="Data manager not initialized"
                )
        
        except Exception as e:
            logger.error(f"Error processing data update request: {str(e)}")
            return render_template('error.html', error=str(e))
    
    # GET request - show form
    return render_template('update_data.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    CODEX: Handle application setup requests.
    """
    if request.method == 'POST':
        # Get form data
        ollama_url = request.form.get('ollama_url', 'http://localhost:11434')
        ollama_model = request.form.get('ollama_model', 'llama3.2')
        alpha_vantage_api_key = request.form.get('alpha_vantage_api_key', '')
        
        try:
            # Update configuration
            if config_manager:
                config_manager.update_config('ai.ollama.url', ollama_url)
                config_manager.update_config('ai.ollama.model', ollama_model)
                config_manager.update_config('data_sources.alpha_vantage.api_key', alpha_vantage_api_key)
                config_manager.save_config()
                
                return render_template(
                    'setup_result.html',
                    success=True,
                    ollama_url=ollama_url,
                    ollama_model=ollama_model
                )
            else:
                return render_template(
                    'error.html',
                    error="Config manager not initialized"
                )
        
        except Exception as e:
            logger.error(f"Error processing setup request: {str(e)}")
            return render_template('error.html', error=str(e))
    
    # GET request - show form
    current_config = {}
    if config_manager:
        current_config = {
            'ollama_url': config_manager.get_config('ai.ollama.url', 'http://localhost:11434'),
            'ollama_model': config_manager.get_config('ai.ollama.model', 'llama3.2'),
            'alpha_vantage_api_key': config_manager.get_config('data_sources.alpha_vantage.api_key', '')
        }
    
    return render_template('setup.html', config=current_config)

@app.route('/api/test', methods=['GET'])
def api_test():
    """
    CODEX: Test API endpoint to check if all components are working.
    """
    components = {
        'config_manager': config_manager is not None,
        'data_manager': data_manager is not None,
        'analysis_engine': analysis_engine is not None,
        'ai_engine': ai_engine is not None,
        'alpha_vantage_api': alpha_vantage_api is not None,
        'b3_api': b3_api is not None
    }
    
    return jsonify({
        'status': 'ok',
        'components': components,
        'timestamp': datetime.now().isoformat()
    })

def run_webui(host='localhost', port=5000, debug=True):
    """
    CODEX: Run the Flask web application.
    
    Args:
        host (str, optional): Host to run the server on. Defaults to 'localhost'.
        port (int, optional): Port to run the server on. Defaults to 5000.
        debug (bool, optional): Whether to run in debug mode. Defaults to True.
    """
    # Initialize components
    initialize_components()
    
    # Create template and static directories if they don't exist
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    
    os.makedirs(template_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    # Run the Flask app
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    # Setup logging
    setup_logging()
    
    # Run the web UI
    run_webui()
