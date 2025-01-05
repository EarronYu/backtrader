import backtrader as bt
from datetime import datetime
import backtrader.indicators as btind


class MyStrategy(bt.Strategy):
    params = (('trix_period', 15), ('rsi_period', 14), ('trix_threshold', 0), ('overbought', 70), ('oversold', 30))

    def __init__(self):
        self.trix = btind.TRIX(self.data.close, period=self.params.trix_period)
        self.rsi = btind.RSI(self.data.close, period=self.params.rsi_period)

    def next(self):
        if self.trix > self.params.trix_threshold:
            if self.rsi > self.params.overbought:
                self.sell()
            elif self.rsi < self.params.oversold:
                self.buy()
        elif self.trix < -self.params.trix_threshold:
            if self.rsi < self.params.oversold:
                self.buy()
            elif self.rsi > self.params.overbought:
                self.sell()
