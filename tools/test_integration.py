import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.offline_backtest import run_backtest
from tools.strategies.rsi_strategy import RSIStrategy
from tools.optimize.optimize_strategies import optimize_rsi_strategy
from tools.report.report_generator import generate_strategy_report

def test_backtest():
    """Test basic backtesting functionality"""
    print("Testing basic backtesting...")
    
    # Test with sample data file
    sample_data_path = os.path.expanduser('~/attachments')
    start_date = datetime(2024, 5, 18)
    end_date = datetime(2024, 5, 19)
    
    results = run_backtest(
        strategy=RSIStrategy,
        symbols=['ENAUSDT'],  # Using symbol from sample data
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        timeframe='15m',
        initial_cash=200000,
        commission=0.0015,
        plot=False,
        use_local_data=True,
        data_path=sample_data_path,
        rsi_period=14,
        rsi_upper=70,
        rsi_lower=30,
        stop_loss_pct=0.05,
        btc_size=0.0005
    )
    
    print(f'Final Portfolio Value: {results[0].broker.getvalue():.2f}')
    return results

def test_optimization():
    """Test strategy optimization with Optuna"""
    print("\nTesting strategy optimization...")
    
    sample_data_path = os.path.expanduser('~/attachments')
    start_date = datetime(2024, 5, 18)
    end_date = datetime(2024, 5, 19)
    
    study = optimize_rsi_strategy(
        symbols=['ENAUSDT'],  # Using symbol from sample data
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        data_path=sample_data_path,
        n_trials=2,  # Small number for testing
        study_name='test_optimization'
    )
    
    print(f'Best trial value: {study.best_value:.4f}')
    print('Best parameters:', study.best_params)
    return study

def test_report_generation(results):
    """Test report generation with QuantStats"""
    print("\nTesting report generation...")
    
    report_path = generate_strategy_report(
        results,
        output_dir='reports',
        title='Test Strategy Report'
    )
    
    print(f'Report generated at: {report_path}')
    return report_path

if __name__ == '__main__':
    # Run basic backtest
    results = test_backtest()
    
    # Generate report
    report_path = test_report_generation(results)
    
    # Run optimization
    study = test_optimization()
    
    print("\nAll tests completed successfully!")
