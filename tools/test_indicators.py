import backtrader as bt

def main():
    print('Backtrader version:', bt.__version__)
    
    print('\nAvailable indicators:')
    for name in dir(bt.indicators):
        if not name.startswith('_'):
            print(f'- {name}')
    
    print('\nTesting SMA creation:')
    cerebro = bt.Cerebro()
    
    # Create a simple data feed
    class TestData(bt.feeds.GenericCSVData):
        params = (
            ('dtformat', '%Y-%m-%d'),
            ('datetime', 0),
            ('open', 1),
            ('high', 2),
            ('low', 3),
            ('close', 4),
            ('volume', 5),
            ('openinterest', -1),
        )
    
    # Create a test strategy
    class TestStrategy(bt.Strategy):
        def __init__(self):
            # Try different SMA initialization patterns
            try:
                self.sma1 = bt.indicators.SMA(self.data0.close)
                print('Success: bt.indicators.SMA')
            except Exception as e:
                print('Failed bt.indicators.SMA:', str(e))
                
            try:
                self.sma2 = bt.ind.SMA(self.data0.close)
                print('Success: bt.ind.SMA')
            except Exception as e:
                print('Failed bt.ind.SMA:', str(e))
                
            try:
                self.sma3 = bt.indicators.MovingAverageSimple(self.data0.close)
                print('Success: bt.indicators.MovingAverageSimple')
            except Exception as e:
                print('Failed bt.indicators.MovingAverageSimple:', str(e))

    cerebro.addstrategy(TestStrategy)
    print('Strategy added successfully')
    
    try:
        cerebro.run()
        print('Strategy run successfully')
    except Exception as e:
        print('Failed to run strategy:', str(e))

if __name__ == '__main__':
    main()
