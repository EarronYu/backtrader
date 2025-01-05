import os
import sys
import pandas as pd
import backtrader as bt
import quantstats

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from offline_backtest import run_backtest
from strategies.rsi_strategy import RSIStrategy

def test_quantstats_report():
    """Test that quantstats report generation works"""
    # Run a minimal backtest just to generate returns
    results = run_backtest(
        strategy=RSIStrategy,
        start_date='2024-05-18',  # Use only the data we have
        end_date='2024-05-18',
        symbols=['ETHUSDT'],
        timeframe='1m',
        compression=1,
        initial_cash=100000,
        commission=0.0015,
        plot=False,
        use_local_data=True,
        data_path='/home/ubuntu/attachments',  # Use the sample data we have
        rsi_period=14,
        rsi_lower=30,
        rsi_upper=70,
        stop_loss_pct=0.05,
        eth_size=0.05
    )
    
    # Verify that the report file was created
    report_path = 'report/backtest_report.html'
    if os.path.exists(report_path):
        print(f"✓ Quantstats report generated successfully at {report_path}")
        print(f"Report file size: {os.path.getsize(report_path)} bytes")
    else:
        print("✗ Failed to generate quantstats report")
        
if __name__ == '__main__':
    test_quantstats_report()
