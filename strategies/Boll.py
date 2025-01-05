import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt


# Create a Stratey
class Boll(bt.Strategy):
    params = (('BBandsperiod', 20),)

    def __init__(self):
        self.dataclose = self.datas[0].close

        self.order = None

        # Add a Bollinger Band indicator
        self.bband = bt.indicators.BBands(self.datas[0], period=self.params.BBandsperiod)

    def next(self):
        if self.order:
            return
        if self.dataclose < self.bband.lines.bot and not self.position:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()
        if self.dataclose > self.bband.lines.top and self.position:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()
