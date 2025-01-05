import backtrader as bt
import pandas as pd
from datetime import datetime

class TestStrategy(bt.Strategy):
    """
    A minimal test strategy to verify indicator initialization
    """
    params = (
        ('sma_period', 20),
        ('rsi_period', 14),
    )

    def __init__(self):
        super().__init__()
        # Create SMA and RSI indicators
        self.sma = bt.indicators.SMA(self.data.close, period=self.p.sma_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)

    def next(self):
        # Just print indicator values
        if len(self) > self.p.sma_period:  # Wait for enough bars
            print(f'Bar {len(self)}: Close={self.data.close[0]:.2f}, SMA={self.sma[0]:.2f}, RSI={self.rsi[0]:.2f}')

def test_backtrader():
    # Create a cerebro instance
    cerebro = bt.Cerebro()
    
    # Load and prepare data
    data = pd.read_csv('/home/ubuntu/attachments/2024-05-18_ETHUSDT_1m.csv', nrows=100)  # Test with small sample
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.set_index('datetime', inplace=True)
    
    # Create a data feed
    data_feed = bt.feeds.PandasData(
        dataname=data,
        datetime=None,  # Use index as datetime
        open=0,         # Column position for open
        high=1,         # Column position for high
        low=2,          # Column position for low
        close=3,        # Column position for close
        volume=4,       # Column position for volume
        openinterest=-1 # Column position for open interest (-1 means not available)
    )
    cerebro.adddata(data_feed)
    
    # Add the test strategy
    cerebro.addstrategy(TestStrategy)
    
    # Set initial cash
    cerebro.broker.setcash(100000.0)
    
    # Run the backtest
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

if __name__ == '__main__':
    test_backtrader()
