# 均线交叉策略
import backtrader as bt


class DualMA(bt.Strategy):
    params = (
        ('nfast', 10),
        ('nslow', 30),
        ('fgPrint', False),
    )

    def __init__(self):
        self.sma_fast = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.nfast)
        self.sma_slow = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.nslow)
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)

    def next(self):
        if self.position:
            if self.crossover < 0:
                self.sell()
        elif self.crossover > 0:
            self.buy()
