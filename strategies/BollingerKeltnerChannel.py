import backtrader as bt
import functions.toolkit as tk
from datetime import datetime
import arrow

# 66 48  3  4
# search_space = {
#     "var1": np.arange(1, 75, 1),
#     "var2": np.arange(0, 5, 0.1),
#     "var3": np.arange(0, 5, 0.1),
#     "var4": np.arange(0, 0.1, 0.01)
# }
class MyStrategy(bt.Strategy):
    params = (
        ('window', 20),
        ('bbdevs', 2),
        ('kcdevs', 1),
        ('bias_pct', 0.05),
    )

    def __init__(self):
        self.kl = self.datas[0]

        self.bb = bt.indicators.BollingerBands(self.kl.close, period=self.params.window, devfactor=self.params.bbdevs)
        self.ma = bt.indicators.SimpleMovingAverage(self.kl.close, period=self.params.window)
        self.atr = bt.indicators.ATR(self.kl, period=self.params.window)
        self.kctop = self.ma + self.params.kcdevs * self.atr
        self.kcbot = self.ma - self.params.kcdevs * self.atr
        self.bbkctop = bt.indicators.Max(self.bb.top, self.kctop)
        self.bbkcbot = bt.indicators.Min(self.bb.bot, self.kcbot)

        self.volatile = bt.indicators.PercentChange(self.kl.open, self.ma)
        self.bias = bt.indicators.PercentChange(self.kl.close, self.ma)

        self.crossuptop = bt.indicators.CrossUp(self.kl.close, self.bbkctop)
        self.crossdownbot = bt.indicators.CrossDown(self.kl.close, self.bbkcbot)
        self.close_long = bt.indicators.CrossDown(self.kl.close, self.bb.mid)
        self.close_short = bt.indicators.CrossUp(self.kl.close, self.bb.mid)
        self.open_long = bt.And(self.crossuptop, self.volatile < 0.05, self.bias <= self.params.bias_pct)
        self.open_short = bt.And(self.crossdownbot, self.volatile < 0.05, self.bias <= self.params.bias_pct)

    def next(self):
        if not self.position:
            if self.open_long:
                self.buy()
            elif self.open_short:
                self.sell()
        else:
            if self.close_long:
                self.close()
            elif self.close_short:
                self.close()
