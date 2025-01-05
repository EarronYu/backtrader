import backtrader as bt

class TestStrategy(bt.Strategy):
    def __init__(self):
        super().__init__()
        self.sma = bt.indicators.SMA(self.data, period=20)
        print('SMA indicator created successfully')

def main():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)
    print('Strategy added successfully')

if __name__ == '__main__':
    main()
