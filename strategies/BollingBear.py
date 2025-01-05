import backtrader as bt


class MyStrategy(bt.Strategy):
    params = dict(
        bollwindow=200,
        devfactor=2,
        bias_pct=0.05
    )

    def __init__(self):
        self.midband = bt.indicators.MovingAverageSimple(
            self.data, period=self.params.bollwindow)
        self.std = bt.indicators.StandardDeviation(
            self.data, period=self.params.bollwindow)
        self.topband = self.midband + self.params.devfactor * self.std
        self.botband = self.midband - self.params.devfactor * self.std
        self.volatile = abs(self.data.open / self.midband - 1)
        self.low_volatile = bt.If(self.volatile < 0.05, 1, 0)
        self.bias = abs(self.data.close / self.midband - 1)
        self.low_bias = bt.If(self.bias <= self.params.bias_pct, 1, 0)
        self.crossuptop = bt.indicators.CrossUp(
            self.data.close, self.topband)
        self.crossdownbot = bt.indicators.CrossDown(
            self.data.close, self.botband)
        self.close_long = bt.indicators.CrossDown(self.data.close, self.midband)
        self.close_short = bt.indicators.CrossUp(self.data.close, self.midband)
        self.open_long = bt.And(self.crossuptop, self.low_volatile, self.low_bias)
        self.open_short = bt.And(self.crossdownbot, self.low_volatile, self.low_bias)

    def next(self):
        if self.open_long:
            self.buy()
        elif self.close_long:
            self.close()
        elif self.open_short:
            self.sell()
        elif self.close_short:
            self.close()
