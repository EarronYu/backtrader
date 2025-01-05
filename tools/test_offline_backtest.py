import os
import sys
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from offline_backtest import run_backtest
from strategies.rsi_strategy import RSIStrategy

def test_offline_backtest():
    """Test offline backtesting with a small ETH/USDT dataset"""
    results = run_backtest(
        strategy=RSIStrategy,
        start_date='2024-05-18',
        end_date='2024-05-18',
        symbols=['ETHUSDT'],
        timeframe='1m',
        compression=1,
        initial_cash=100000,
        commission=0.0015,
        plot=False,
        use_local_data=True,
        data_path='/home/ubuntu/attachments',
        rsi_period=14,
        rsi_lower=30,
        rsi_upper=70,
        stop_loss_pct=0.05,
        btc_size=0.0005,
        eth_size=0.05
    )
    return results

if __name__ == '__main__':
    test_offline_backtest()
