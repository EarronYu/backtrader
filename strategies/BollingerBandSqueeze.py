
import backtrader as bt


class MyStrategy(bt.Strategy):
    lines = ('squeeze', 'buy', 'sell')
    params = (('window', 20), ('bbdevs', 2.0), ('kcdevs', 1.5), ('movav', bt.ind.MovAv.Simple),)
    plotinfo = dict(subplot=True)

    def __init__(self):
        bb = bt.ind.BollingerBands(
            period=self.p.window, devfactor=self.p.bbdevs, movav=self.p.movav)
        kc = KeltnerChannel(
            period=self.p.window, devfactor=self.p.kcdevs, movav=self.p.movav)
        self.lines.squeeze = bb.top - kc.top

    def next(self):
        if not self.position:
            if self.lines.squeeze[0] < 0:
                self.lines.buy[0] = 1
                self.lines.sell[0] = 0
                self.buy()
            else:
                self.lines.buy[0] = 0
                self.lines.sell[0] = 1
                self.sell()


class KeltnerChannel(bt.Indicator):
    lines = ('mb', 'top', 'bot',)
    params = (('period', 20), ('devfactor', 1.5), ('movav', bt.ind.MovAv.Simple),)
    plotinfo = dict(subplot=False)

    def __init__(self):
        self.lines.mid = ma = self.p.movav(self.data, period=self.p.period)
        self.p.devfactor = self.p.devfactor.astype(float)
        atr = self.p.devfactor * bt.ind.ATR(self.data, period=self.p.period)
        self.lines.top = ma + atr
        self.lines.bot = ma - atr
