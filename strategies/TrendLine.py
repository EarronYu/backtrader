from backtrader import Indicator
import datetime
import time
import backtrader as bt


class MyStrategy(bt.Strategy):
    lines = ('signal', 'trend')
    params = (
        ('x1', None),
        ('y1', None),
        ('x2', None),
        ('y2', None)
    )

    def __init__(self):
        self.p.x1 = datetime.datetime.strptime(self.p.x1, "%Y-%m-%d %H:%M:%S")
        self.p.x2 = datetime.datetime.strptime(self.p.x2, "%Y-%m-%d %H:%M:%S")
        x1_time_stamp = time.mktime(self.p.x1.timetuple())
        x2_time_stamp = time.mktime(self.p.x2.timetuple())
        self.m = self.get_slope(x1_time_stamp, x2_time_stamp, self.p.y1, self.p.y2)
        self.B = self.get_y_intercept(self.m, x1_time_stamp, self.p.y1)

    def next(self):
        date = self.data.datetime.datetime()
        date_timestamp = time.mktime(date.timetuple())
        Y = self.get_y(date_timestamp)
        self.lines.trend[0] = Y
        # Check if price has crossed up / down into it.
        if self.data.high[0] > Y and self.data.low[-1] < Y:
            self.lines.signal[0] = 1
            self.buy()
        # Check for cross downs (Into support)
        elif self.data.low[0] < Y and self.data.high[-1] > Y:
            self.lines.signal[0] = -1
            self.sell()
        else:
            self.lines.signal[0] = 0

    def get_slope(self, x1, x2, y1, y2):
        m = (y2 - y1) / (x2 - x1)
        return m

    def get_y_intercept(self, m, x1, y1):
        b = y1 - m * x1
        return b

    def get_y(self, x):
        return self.m * x + self.B


