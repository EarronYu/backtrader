import backtrader as bt


class BollingBear(bt.Strategy):
    params = (
        ('period', 20),  # 布林带周期
        ('devfactor', 2),  # 标准差倍数
        ('size', 1),  # 交易数量
        ('stop_loss_pct', 0.02),  # 止损百分比
    )

    def __init__(self):
        # 计算布林带指标
        self.boll = bt.indicators.BollingerBands(
            self.data.close, 
            period=self.params.period,
            devfactor=self.params.devfactor
        )
        
        # 跟踪订单和持仓
        self.order = None
        self.price_entry = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 当价格触及下轨时买入
            if self.data.close[0] <= self.boll.lines.bot[0]:
                self.order = self.buy(size=self.params.size)
                self.price_entry = self.data.close[0]
        
        else:
            # 当价格触及上轨时卖出
            if self.data.close[0] >= self.boll.lines.top[0]:
                self.order = self.sell(size=self.params.size)
            
            # 止损
            if self.data.close[0] < self.price_entry * (1 - self.params.stop_loss_pct):
                self.order = self.sell(size=self.params.size)
