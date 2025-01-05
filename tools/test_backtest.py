import backtrader as bt
from backtest_runner import run_backtest, print_backtest_results
from strategies.rsi_strategy import RSIStrategy

def test_backtest():
    """Test the backtest runner with RSI strategy."""
    strategy = run_backtest(
        strategy_cls=RSIStrategy,
        data_path='data/BTCUSDT-1m-2023.csv',
        start_date='2023-01-01',
        end_date='2023-12-31',
        timeframe='1m',
        params={
            'rsi_period': 14,
            'sma_period1': 20,
            'sma_period2': 50,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
    )
    
    # Print results
    print_backtest_results(strategy)

if __name__ == '__main__':
    test_backtest()
