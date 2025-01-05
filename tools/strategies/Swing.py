from backtrader import Indicator, LineBuffer
import backtrader as bt


class MyStrategy(bt.Strategy):
    lines = ('swings', 'signal')
    params = (('period', 20),)

    def __init__(self):
        self.swing_range = (self.p.period * 2) + 1
        self.addminperiod(self.swing_range)

        self.lines.swings = LineBuffer(self.swing_range)
        self.lines.signal = LineBuffer(1)

    def next(self):
        highs = self.data.high.get(size=self.swing_range)
        lows = self.data.low.get(size=self.swing_range)

        if highs.pop(self.p.period) > max(highs):
            self.lines.swings[0] = 1
            self.lines.signal[0] = 1
            self.buy()
        elif lows.pop(self.p.period) < min(lows):
            self.lines.swings[0] = -1
            self.lines.signal[0] = -1
            self.sell()
        else:
            self.lines.swings[0] = 0
            self.lines.signal[0] = 0

