import backtrader as bt
from strategies.rsi_strategy import RSIStrategy
from binance_store import BinanceStore
import datetime

def test_rsi_strategy():
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Add the RSI strategy
    cerebro.addstrategy(RSIStrategy)
    
    # Create a Data Feed
    store = BinanceStore()
    data = store.get_data(
        dataname='BTCUSDT',
        timeframe='1m',
        fromdate=datetime.datetime(2024, 1, 1),
        todate=datetime.datetime(2024, 1, 2)
    )
    
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)
    
    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Run over everything
    cerebro.run()
    
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

if __name__ == '__main__':
    test_rsi_strategy()
