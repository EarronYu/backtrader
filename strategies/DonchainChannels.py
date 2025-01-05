from datetime import datetime
import backtrader as bt


class DonchainChannels(bt.Indicator):
    """
    Params Note:
      - `lookback` (default: -1)
        If `-1`, the bars to consider will start 1 bar in the past and the
        current high/low may break through the channel.
        If `0`, the current prices will be considered for the Donchian
        Channel. This means that the price will **NEVER** break through the
        upper/lower channel bands.
    """
    alias = ('DCH', 'DonchianChannel',)
    lines = ('dcm', 'dch', 'dcl',)  # dc middle, dc high, dc low
    params = dict(
        period=20,
        lookback=-1,  # consider current bar or not
    )
    plotinfo = dict(subplot=False)  # plot along with data
    plotlines = dict(
        dcm=dict(ls='--'),  # dashed line
        dch=dict(_samecolor=True),  # use same color as prev line (dcm)
        dcl=dict(_samecolor=True),  # use same color = prev line (dch)
    )

    def __init__(self):
        hi, lo = self.data.high, self.data.low
        if self.params.lookback:  # move backwards as needed
            hi, lo = hi(self.params.lookback), lo(self.params.lookback)
        self.l.dch = bt.indicators.Highest(hi, period=self.params.period)
        self.l.dcl = bt.indicators.Lowest(lo, period=self.params.period)
        self.l.dcm = (self.l.dch + self.l.dcl) / 2.0  # avg of the above


class MyStrategy(bt.Strategy):
    def __init__(self):
        self.myind = DonchainChannels()

    def next(self):
        if self.data[0] > self.myind.dch[0] and not self.position:
            self.log('BUY CREATE, %.2f' % self.data[0])
            self.buy()
        elif self.data[0] < self.myind.dcl[0] and self.position:
            self.log('SELL CREATE, %.2f' % self.data[0])
            self.sell()

