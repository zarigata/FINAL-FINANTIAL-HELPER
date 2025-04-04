#!/usr/bin/env python3
# ███████╗██╗███╗   ██╗██████╗  ██████╗ ████████╗
# ██╔════╝██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
# █████╗  ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
# ██╔══╝  ██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
# ██║     ██║██║ ╚████║██████╔╝╚██████╔╝   ██║   
# ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
# CLI TEST SCRIPT v1.0
# CODEX: This script tests the CLI functionality of the FinBot application.
# CODEX: It simulates command-line arguments and tests the CLI responses.

import os
import sys
import argparse
from rich.console import Console

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the CLI module
from src.cli import CLIManager

def create_mock_args(command, **kwargs):
    """
    CODEX: Create a mock args object for testing.
    
    Args:
        command (str): Command name
        **kwargs: Command arguments
    
    Returns:
        argparse.Namespace: Mock args object
    """
    args = argparse.Namespace()
    args.command = command
    
    for key, value in kwargs.items():
        setattr(args, key, value)
    
    return args

def test_invest_command():
    """
    CODEX: Test the 'invest' command.
    """
    console = Console()
    cli_manager = CLIManager(console)
    
    # Create mock args
    args = create_mock_args(
        command="invest",
        amount=10000,
        market="US",
        type="stocks",
        goal=1000000,
        years=30,
        risk="moderate"
    )
    
    # Test the command
    console.print("\n[bold]Testing 'invest' command:[/bold]")
    cli_manager.handle_invest_command(args)

def test_analyze_command():
    """
    CODEX: Test the 'analyze' command.
    """
    console = Console()
    cli_manager = CLIManager(console)
    
    # Create mock args
    args = create_mock_args(
        command="analyze",
        market="US",
        type="stocks",
        symbol="AAPL",
        period="1y"
    )
    
    # Test the command
    console.print("\n[bold]Testing 'analyze' command:[/bold]")
    cli_manager.handle_analyze_command(args)

def test_update_data_command():
    """
    CODEX: Test the 'update-data' command.
    """
    console = Console()
    cli_manager = CLIManager(console)
    
    # Create mock args
    args = create_mock_args(
        command="update-data",
        market="BOTH",
        force=True
    )
    
    # Test the command
    console.print("\n[bold]Testing 'update-data' command:[/bold]")
    cli_manager.handle_update_data_command(args)

def test_setup_command():
    """
    CODEX: Test the 'setup' command.
    """
    console = Console()
    cli_manager = CLIManager(console)
    
    # Create mock args
    args = create_mock_args(
        command="setup",
        ollama_url="http://localhost:11434",
        ollama_model="llama3.2",
        reset_config=False
    )
    
    # Test the command
    console.print("\n[bold]Testing 'setup' command:[/bold]")
    cli_manager.handle_setup_command(args)

def test_portfolio_command():
    """
    CODEX: Test the 'portfolio' command.
    """
    console = Console()
    cli_manager = CLIManager(console)
    
    # Create mock args
    args = create_mock_args(
        command="portfolio",
        action="create",
        name="MyPortfolio"
    )
    
    # Test the command
    console.print("\n[bold]Testing 'portfolio' command:[/bold]")
    cli_manager.handle_portfolio_command(args)

def main():
    """
    CODEX: Main function to run all tests.
    """
    console = Console()
    
    console.print(Panel.fit(
        "[bold cyan]FinBot CLI Test Script[/bold cyan]",
        border_style="cyan"
    ))
    
    # Run tests
    test_invest_command()
    test_analyze_command()
    test_update_data_command()
    test_setup_command()
    test_portfolio_command()
    
    console.print("\n[bold green]All tests completed![/bold green]")

if __name__ == "__main__":
    main()
