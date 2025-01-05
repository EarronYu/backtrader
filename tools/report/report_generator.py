import os
import pandas as pd
import quantstats as qs
import logging
from datetime import datetime

def generate_strategy_report(
    results,
    output_dir='reports',
    filename=None,
    benchmark_symbol='SPY',
    title=None
):
    """
    Generate a detailed strategy performance report using QuantStats
    
    Args:
        results: Backtrader cerebro.run() results
        output_dir: Directory to save the report
        filename: Custom filename for the report (default: auto-generated based on date)
        benchmark_symbol: Symbol to use as benchmark (default: SPY)
        title: Custom title for the report
    
    Returns:
        str: Path to the generated report
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the first strategy instance
        strategy = results[0]
        
        # Get portfolio analysis from PyFolio analyzer
        portfolio_stats = strategy.analyzers.getbyname('pyfolio')
        returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
        
        # Convert timezone-aware datetime to timezone-naive
        returns.index = returns.index.tz_localize(None)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'strategy_report_{timestamp}.html'
        
        # Ensure .html extension
        if not filename.endswith('.html'):
            filename += '.html'
        
        output_path = os.path.join(output_dir, filename)
        
        # Generate title if not provided
        if title is None:
            title = 'Trading Strategy Performance Analysis'
        
        # Calculate key metrics
        total_return = (strategy.broker.getvalue() / strategy.broker.startingcash - 1) * 100
        sharpe = strategy.analyzers.sharpe.get_analysis()['sharperatio']
        drawdown = strategy.analyzers.drawdown.get_analysis()['max']['drawdown']
        
        # Log key metrics
        logging.info(f'\n=== Strategy Performance Metrics ===')
        logging.info(f'Total Return: {total_return:.2f}%')
        logging.info(f'Sharpe Ratio: {sharpe:.2f}')
        logging.info(f'Max Drawdown: {drawdown:.2f}%')
        
        # Generate HTML report
        qs.reports.html(
            returns=returns,
            output=output_path,
            title=title,
            benchmark=benchmark_symbol
        )
        
        logging.info(f'Report generated successfully: {output_path}')
        return output_path
        
    except Exception as e:
        logging.error(f'Error generating report: {str(e)}')
        raise

def generate_optimization_report(
    study,
    output_dir='reports',
    filename=None
):
    """
    Generate a report for optimization results using QuantStats
    
    Args:
        study: Optuna study object containing optimization results
        output_dir: Directory to save the report
        filename: Custom filename for the report
    
    Returns:
        str: Path to the generated report
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'optimization_report_{timestamp}.html'
            
        # Ensure .html extension
        if not filename.endswith('.html'):
            filename += '.html'
            
        output_path = os.path.join(output_dir, filename)
        
        # Create DataFrame with trial results
        trials_df = study.trials_dataframe()
        
        # Generate HTML content
        html_content = f"""
        <html>
        <head>
            <title>Strategy Optimization Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .best {{ background-color: #e6ffe6; }}
            </style>
        </head>
        <body>
            <h1>Strategy Optimization Report</h1>
            <h2>Best Trial Results</h2>
            <p>Best Value: {study.best_value:.4f}</p>
            <h3>Best Parameters:</h3>
            <ul>
        """
        
        for param, value in study.best_trial.params.items():
            html_content += f"    <li>{param}: {value}</li>\n"
            
        html_content += """
            </ul>
            <h2>All Trials</h2>
        """
        
        # Add trials DataFrame to HTML
        html_content += trials_df.to_html(classes='dataframe')
        html_content += """
        </body>
        </html>
        """
        
        # Write HTML file
        with open(output_path, 'w') as f:
            f.write(html_content)
            
        logging.info(f'Optimization report generated successfully: {output_path}')
        return output_path
        
    except Exception as e:
        logging.error(f'Error generating optimization report: {str(e)}')
        raise

if __name__ == '__main__':
    # Example usage
    from ..offline_backtest import run_backtest
    from ..strategies.rsi_strategy import RSIStrategy
    
    # Run backtest
    results = run_backtest(
        strategy=RSIStrategy,
        symbols=['BTCUSDT'],
        start_date='2024-01-01',
        end_date='2024-02-01',
        timeframe='15m',
        initial_cash=200000,
        commission=0.0015,
        plot=False,
        use_local_data=True,
        data_path='\\\\znas\\Main\\spot',
        rsi_period=14,
        rsi_buy=30,
        rsi_sell=70,
        stop_loss_pct=0.05,
        btc_size=0.0005
    )
    
    # Generate strategy report
    report_path = generate_strategy_report(
        results,
        output_dir='reports',
        title='RSI Strategy Analysis'
    )
    print(f'Report generated: {report_path}')
