import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime as dt
from datetime import timezone
import pandas as pd
import backtrader as bt
from backtrader import TimeFrame
from backtrader.comminfo import CommInfoBase
from backtrader.filters import HeikinAshi
import backtrader.analyzers as btanalyzers
import warnings
import quantstats
import numpy as np

from binance_store import BinanceStore
from tools.strategies.BollingBear import BollingBear

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'report')

class CommInfoFractional(CommInfoBase):
    """
    Commission model that supports fractional sizes and percentage-based commission
    """
    params = dict(
        commission=0.0015,  # Default commission 0.15%
        mult=1.0,          # Multiplier
        margin=None,       # Margin
        commtype=bt.CommInfoBase.COMM_PERC,  # Commission type: percentage
        percabs=True,      # Absolute percentage
    )
    
    def getsize(self, price, cash):
        """Returns fractional size for cash amount"""
        return self.p.mult * cash / price

    def _getcommission(self, size, price, pseudoexec):
        """Returns commission for a given trade"""
        return abs(size) * price * self.p.commission  # Use abs() for short positions

def run_backtest(
    strategy,
    start_date=None,
    end_date=None,
    symbols=['BTCUSDT', 'ETHUSDT'],
    timeframe='1m',
    compression=1,
    initial_cash=200000,
    commission=0.0015,
    plot=True,
    use_local_data=True,  # Default to using local data
    data_path='\\\\znas\\Main\\spot',  # Default local data path
    **strategy_params
):
    """
    Integrated backtesting function
    
    Parameters:
        strategy: Strategy class
        start_date: Start date (str or datetime, format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS')
        end_date: End date (str or datetime, format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS')
        symbols: List of trading pairs
        timeframe: Time period ('1m', '5m', '15m', '1h', '4h', '1d', etc.)
        compression: K-line period compression multiplier
        initial_cash: Initial capital
        commission: Commission rate
        plot: Whether to plot
        use_local_data: Whether to use local data (default True)
        data_path: Local data path
        strategy_params: Strategy parameters
    """
    # Handle date parameters
    if isinstance(start_date, str):
        try:
            start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            start_date = dt.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        start_date = start_date.replace(tzinfo=timezone.utc)
    
    if isinstance(end_date, str):
        try:
            end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            end_date = dt.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
        end_date = end_date.replace(tzinfo=timezone.utc)
    
    # Default to 30 days ago if no start date
    if start_date is None:
        start_date = dt.datetime.now(timezone.utc) - dt.timedelta(days=30)
    
    # Default to current time if no end date
    if end_date is None:
        end_date = dt.datetime.now(timezone.utc)
        
    # Timeframe mapping
    timeframe_map = {
        '1m': (TimeFrame.Minutes, 1),
        '5m': (TimeFrame.Minutes, 5),
        '15m': (TimeFrame.Minutes, 15),
        '30m': (TimeFrame.Minutes, 30),
        '1h': (TimeFrame.Minutes, 60),
        '4h': (TimeFrame.Minutes, 240),
        '1d': (TimeFrame.Days, 1),
    }
    
    tf, comp = timeframe_map.get(timeframe, (TimeFrame.Minutes, 1))
    comp *= compression  # Apply compression multiplier
    
    cerebro = bt.Cerebro()
    
    # Set capital and commission
    cerebro.broker.setcash(initial_cash)
    # Set commission info
    comminfo = CommInfoFractional()
    comminfo.p.commission = commission  # Update commission from parameter
    cerebro.broker.addcommissioninfo(comminfo)
    
    # Create BinanceStore for local data handling
    store = BinanceStore(coin_target='USDT')
    
    # Modify data acquisition part
    for symbol in symbols:
        if use_local_data:
            data = store.getlocaldata(
                timeframe=tf,
                compression=comp,
                dataname=symbol,
                start_date=start_date,
                end_date=end_date,
                datapath=data_path
            )
        else:
            data = store.getdata(
                timeframe=tf,
                compression=comp,
                dataname=symbol,
                start_date=start_date,
                end_date=end_date,
                LiveBars=False
            )
            
        if data is None:  # If data acquisition fails
            print(f"Unable to get data for {symbol}, skipping")
            continue
            
        # Add HeikinAshi filter
        if strategy_params.get('use_ha', False):
            data_ha = data.clone()
            data_ha.addfilter(HeikinAshi(data_ha))
            cerebro.adddata(data_ha, name=f"{symbol}_HA")
        cerebro.adddata(data, name=symbol)
    
    # Add analyzers in correct order
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio',
                       timeframe=TimeFrame.Minutes,
                       compression=comp)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe',
                       riskfreerate=0.0,
                       timeframe=TimeFrame.Minutes)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    # Add observers for trade tracking
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.DrawDown)
    
    # Create report directory
    os.makedirs('report', exist_ok=True)
    
    # Add strategy
    cerebro.addstrategy(strategy, **strategy_params)
    
    # Run backtest
    results = cerebro.run()
    strat = results[0]
    
    # Output statistics
    portfolio_value = cerebro.broker.getvalue()
    roi = (portfolio_value - initial_cash) / initial_cash * 100
    
    print(f'\n=== Backtest Results ===')
    print(f'Initial Capital: {initial_cash:,.2f}')
    print(f'Final Capital: {portfolio_value:,.2f}')
    print(f'ROI: {roi:.2f}%')
    try:
        sharpe_analysis = strat.analyzers.sharpe.get_analysis()
        sharpe_ratio = sharpe_analysis.get("sharperatio", 0.0)
        if sharpe_ratio is None:
            sharpe_ratio = 0.0
        print(f'Sharpe Ratio: {sharpe_ratio:.2f}')
    except Exception as e:
        print('Sharpe Ratio: 0.00')
    drawdown_analysis = strat.analyzers.drawdown.get_analysis()
    max_drawdown = drawdown_analysis.get("max", {}).get("drawdown", 0.0)
    print(f'Max Drawdown: {max_drawdown:.2f}%')
    
    # Generate quantstats report
    try:
        portfolio_stats = strat.analyzers.getbyname('pyfolio')
        
        # 创建完整的日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # 获取收益数据并正确处理
        returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
        
        # 确保返回值是日频的
        if returns is not None and not returns.empty:
            # 转换为日频数据
            returns = returns.resample('D').sum()  # 使用 sum() 而不是 agg()
        else:
            # 如果没有交易，创建空的日频收益序列
            returns = pd.Series(0, index=date_range)
            returns.iloc[0] = 0.0001  # 添加小的非零值
        
        # 确保数据有效
        returns = returns.fillna(0)
        returns = returns.replace([np.inf, -np.inf], 0)
        
        # 生成报告
        os.makedirs(REPORT_DIR, exist_ok=True)
        report_path = os.path.join(REPORT_DIR, 'backtest_report.html')
        
        # 使用正确处理后的收益数据生成报告
        quantstats.reports.html(
            returns=returns,
            output=report_path,
            title='Trading Strategy Analysis'
        )
        
        # 打印统计信息
        print("\n=== Returns Statistics ===")
        print(f"Total Returns: {returns.sum():.2%}")
        print(f"Average Daily Return: {returns.mean():.2%}")
        print(f"Return Volatility: {returns.std():.2%}")
        if returns.std() != 0:
            print(f"Sharpe Ratio: {(returns.mean() / returns.std() * np.sqrt(252)):.2f}")
        else:
            print("Sharpe Ratio: N/A (zero volatility)")
        
    except Exception as e:
        print(f"Warning: Could not generate quantstats report: {str(e)}")
        print(f"Returns shape: {returns.shape if 'returns' in locals() else 'N/A'}")
        if 'returns' in locals():
            print(f"Returns head:\n{returns.head()}")
            print(f"Returns statistics:\n{returns.describe()}")
    
    return results
    
    # Plot
    if plot:
        cerebro.plot(style='candlestick')
    
    return results

if __name__ == '__main__':
    # Example usage
    results = run_backtest(
        strategy=BollingBear,
        start_date='2023-01-01',
        end_date='2024-06-01',
        symbols=['BTCUSDT'],
        timeframe='15m',
        compression=1,
        initial_cash=200000,
        commission=0.0015,
        plot=True,
        use_local_data=True,
        data_path='\\\\znas\\Main\\spot',
        # Strategy parameters - 只使用BollingBear支持的参数
        period=20,          # 布林带周期
        devfactor=2,        # 标准差倍数
        size=1,             # 交易数量
        stop_loss_pct=0.02  # 止损百分比
    )
