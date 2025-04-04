#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# MAIN SCRIPT v1.0
# CODEX: This is the main entry point for the FinBot application.
# CODEX: It handles command-line arguments and orchestrates the workflow.

import argparse
import os
import sys
import platform
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import internal modules
from src.config import ConfigManager
from src.cli import CLIManager
from src.data import DataManager
from src.analysis import AnalysisEngine
from src.ai import AIEngine
from src.utils import setup_logging, create_directories

def main():
    """
    CODEX: Main entry point for the FinBot application.
    CODEX: Parses command line arguments and routes to appropriate handlers.
    """
    # Initialize console for rich output
    console = Console()
    
    # Display welcome banner
    display_banner(console)
    
    # Setup initial environment
    setup_environment(console)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize CLI manager
    cli_manager = CLIManager(console)
    
    # Route to appropriate command handler
    try:
        if args.command == "invest":
            cli_manager.handle_invest_command(args)
        elif args.command == "analyze":
            cli_manager.handle_analyze_command(args)
        elif args.command == "update-data":
            cli_manager.handle_update_data_command(args)
        elif args.command == "setup":
            cli_manager.handle_setup_command(args)
        elif args.command == "portfolio":
            cli_manager.handle_portfolio_command(args)
        else:
            console.print("[bold red]Unknown command.[/bold red] Use --help to see available commands.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        console.print("[yellow]For more details, check the log file.[/yellow]")
        return 1
    
    return 0

def parse_arguments():
    """
    CODEX: Parse command line arguments for the application.
    CODEX: Defines all available commands and their parameters.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="FinBot - AI-Powered Financial Investment Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Invest command
    invest_parser = subparsers.add_parser("invest", help="Get investment recommendations")
    invest_parser.add_argument("--amount", type=float, required=True, help="Amount to invest")
    invest_parser.add_argument("--market", choices=["US", "BR", "BOTH"], required=True, help="Target market")
    invest_parser.add_argument("--type", choices=["stocks", "bonds", "savings", "mixed"], required=True, help="Investment type")
    invest_parser.add_argument("--goal", type=float, help="Target amount to reach")
    invest_parser.add_argument("--years", type=int, help="Investment timeline in years")
    invest_parser.add_argument("--risk", choices=["conservative", "moderate", "aggressive"], default="moderate", help="Risk tolerance")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze market or specific assets")
    analyze_parser.add_argument("--market", choices=["US", "BR", "BOTH"], required=True, help="Target market")
    analyze_parser.add_argument("--type", choices=["stocks", "bonds", "savings", "market"], required=True, help="Analysis type")
    analyze_parser.add_argument("--symbol", help="Specific symbol to analyze (optional)")
    analyze_parser.add_argument("--period", choices=["1d", "1w", "1m", "3m", "6m", "1y", "5y", "max"], default="1y", help="Analysis period")
    
    # Update data command
    update_parser = subparsers.add_parser("update-data", help="Update market data")
    update_parser.add_argument("--market", choices=["US", "BR", "BOTH"], default="BOTH", help="Market to update")
    update_parser.add_argument("--force", action="store_true", help="Force update even if data is recent")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup or configure the application")
    setup_parser.add_argument("--ollama-url", help="URL for Ollama API")
    setup_parser.add_argument("--ollama-model", help="Model to use with Ollama")
    setup_parser.add_argument("--reset-config", action="store_true", help="Reset configuration to defaults")
    
    # Portfolio command
    portfolio_parser = subparsers.add_parser("portfolio", help="Manage investment portfolio")
    portfolio_parser.add_argument("--action", choices=["create", "view", "update", "optimize"], required=True, help="Portfolio action")
    portfolio_parser.add_argument("--name", help="Portfolio name")
    
    return parser.parse_args()

def setup_environment(console):
    """
    CODEX: Set up the application environment.
    CODEX: Creates necessary directories and initializes configuration.
    
    Args:
        console (rich.console.Console): Console for output
    """
    try:
        # Create necessary directories
        create_directories()
        
        # Initialize configuration
        config = ConfigManager()
        
        # Setup logging
        setup_logging(config.get_logging_config())
        
        # Check for Ollama availability
        ai_engine = AIEngine(config.get_ollama_config())
        if not ai_engine.check_ollama_availability():
            console.print("[bold yellow]Warning:[/bold yellow] Ollama is not available. Some features may be limited.")
        
        # Initialize database
        data_manager = DataManager(config.get_database_config())
        data_manager.initialize_database()
        
    except Exception as e:
        console.print(f"[bold red]Error setting up environment:[/bold red] {str(e)}")
        console.print("Please run 'python finbot.py setup' to configure the application.")

def display_banner(console):
    """
    CODEX: Display the application banner.
    
    Args:
        console (rich.console.Console): Console for output
    """
    banner = """
    ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
    ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
    █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
    ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
    ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
    """
    
    console.print(Panel.fit(
        f"[bold cyan]{banner}[/bold cyan]\n[bold green]AI-Powered Financial Investment Assistant[/bold green]",
        border_style="green"
    ))
    
    # Display system information
    system_info = Table.grid(padding=(0, 1))
    system_info.add_row("Version:", "[cyan]1.0.0[/cyan]")
    system_info.add_row("Platform:", f"[cyan]{platform.system()} {platform.release()}[/cyan]")
    system_info.add_row("Python:", f"[cyan]{platform.python_version()}[/cyan]")
    
    console.print(system_info)
    console.print("")

if __name__ == "__main__":
    sys.exit(main())
