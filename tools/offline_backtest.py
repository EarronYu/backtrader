import datetime as dt
from datetime import timezone
import os
import pandas as pd
import backtrader as bt
from backtrader import TimeFrame
from backtrader.comminfo import CommInfoBase
from backtrader.filters import HeikinAshi
import backtrader.analyzers as btanalyzers
import warnings
import quantstats

from binance_store import BinanceStore
from strategies.rsi_strategy import RSIStrategy

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
        
        # Create a complete date range for the backtest period
        date_range = pd.date_range(start=start_date, end=end_date, freq='1D')
        
        try:
            if portfolio_stats is None:
                print("Warning: PyFolio analyzer not found")
                returns = pd.Series([0.0] * len(date_range), index=date_range)
            else:
                returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
                if returns is None or (hasattr(returns, 'empty') and returns.empty):
                    print("Warning: No trades were made during the backtest period")
                    # Use a tiny non-zero return to prevent division by zero
                    returns = pd.Series([0.0001] + [0.0] * (len(date_range)-1), index=date_range)
                else:
                    # Convert timezone-aware index to timezone-naive
                    returns.index = returns.index.tz_localize(None)
                    # Convert minute returns to daily returns if needed
                    if returns.index.freq != 'D':
                        returns = returns.resample('D').agg('sum')
                    # Reindex to ensure we have data for the full period
                    returns = returns.reindex(date_range, fill_value=0.0)
                    # If all returns are zero, add a tiny non-zero return
                    if (returns == 0).all():
                        returns.iloc[0] = 0.0001
        except Exception as e:
            print(f"Warning: Error getting PyFolio items: {str(e)}")
            returns = pd.Series([0.0] * len(date_range), index=date_range)
            
        # Ensure we have at least two data points
        if len(returns) < 2:
            print("Warning: Adding extra day for minimum data requirements")
            extra_date = date_range[-1] + pd.Timedelta(days=1)
            returns[extra_date] = 0.0
        
        # Ensure returns are properly formatted for quantstats
        # Reuse the date_range we created earlier to ensure proper frequency
        returns = pd.Series(
            returns.reindex(date_range, method='ffill').values,
            index=date_range,
            dtype=float
        )
        
        # Create report directory if it doesn't exist
        os.makedirs('report', exist_ok=True)
        
        # Save report to tools/report directory
        report_path = 'report/backtest_report.html'
        try:
            quantstats.reports.html(returns, output=report_path, title='Trading Strategy Analysis',
                                  download_filename=None)  # Prevent download attempts
            print(f"\nQuantstats report generated: {report_path}")
        except Exception as e:
            print(f"Warning: Could not generate quantstats report: {str(e)}")
            print(f"Returns shape: {returns.shape}")
            print(f"Returns head: {returns.head()}")
            print(f"Returns dtype: {returns.dtype}")
        print(f"\nQuantstats report generated: {report_path}")
    except Exception as e:
        print(f"Warning: Could not generate quantstats report: {str(e)}")
        print(f"Returns shape: {returns.shape if 'returns' in locals() else 'N/A'}")
        print(f"Returns head: {returns.head() if 'returns' in locals() else 'N/A'}")
    
    return results
    
    # Plot
    if plot:
        cerebro.plot(style='candlestick')
    
    return results

if __name__ == '__main__':
    # Example usage
    results = run_backtest(
        strategy=RSIStrategy,
        start_date='2024-01-01',
        end_date='2024-02-01',
        symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        timeframe='15m',
        compression=1,
        initial_cash=200000,
        commission=0.0015,
        plot=True,
        use_local_data=True,
        data_path='\\\\znas\\Main\\spot',
        # Strategy parameters
        rsi_period=14,
        rsi_lower=30,
        rsi_upper=70,
        stop_loss_pct=0.05,
        btc_size=0.0005,
        eth_size=0.05
    )
