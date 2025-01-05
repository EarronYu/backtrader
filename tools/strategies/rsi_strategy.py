import backtrader as bt
import backtrader.indicators as btind

class RSIStrategy(bt.Strategy):
    """
    RSI Strategy implementation based on user's requirements
    """
    params = (
        ('coin_target', ''),
        ('timeframe', ''),
        ('rsi_period', 14),        # RSI period
        ('rsi_lower', 30),        # RSI buy threshold 
        ('rsi_upper', 70),        # RSI sell threshold
        ('stop_loss_pct', 0.05),  # Stop loss percentage
        ('btc_size', 0.0005),     # BTC default trade size
        ('eth_size', 0.05),       # ETH default trade size
    )

    def __init__(self):
        self.orders = {}
        for d in self.datas:
            self.orders[d._name] = None

        # Create indicators
        self.sma1 = {}
        self.sma2 = {}
        self.rsi = {}
        for i in range(len(self.datas)):
            ticker = self.datas[i]._name
            # Create indicators for each data feed
            # Create indicators using btind namespace
            self.sma1[ticker] = btind.SMA(self.datas[i], period=8)
            self.sma2[ticker] = btind.SMA(self.datas[i], period=16)
            self.rsi[ticker] = btind.RSI(self.datas[i], period=self.p.rsi_period)
            
        # Track buy price for stop loss
        self.buy_price = {}

    def next(self):
        for data in self.datas:
            ticker = data._name
            order = self.orders[data._name]
            
            # Check if we have an existing order
            if order and order.status == bt.Order.Submitted:
                if order and order.status == bt.Order.Submitted:
                    return

                position = self.getposition(data)
                
                # Check stop loss if we have a position
                if position:
                    unrealized_pnl = (data.close[0] - self.buy_price[ticker]) / self.buy_price[ticker]
                    if unrealized_pnl < -self.p.stop_loss_pct:
                        print(f"\t - Stop loss triggered: {ticker} Current loss: {unrealized_pnl:.2%}")
                        self.orders[data._name] = self.close(data=data)
                        return

                if not position:  # Not in market
                    if order and order.status == bt.Order.Accepted:
                        print(f"\t - Cancel the order {order.ref} to buy {data._name}")
                        
                    # Buy if RSI is below threshold and SMA8 above SMA16
                    if (self.rsi[ticker][0] < self.p.rsi_lower and 
                        self.sma1[ticker][0] > self.sma2[ticker][0]):
                        
                        size = self.p.btc_size
                        if data._name == "ETHUSDT": 
                            size = self.p.eth_size

                        price = data.close[0]
                        self.buy_price[ticker] = price

                        print(f" - Buy {ticker} size = {size} at price = {price}")
                        self.orders[data._name] = self.buy(data=data, 
                                                       exectype=bt.Order.Limit,
                                                       price=price, 
                                                       size=size)

                else:  # In market
                    # Sell if RSI is above threshold or SMA8 below SMA16
                    if (self.rsi[ticker][0] > self.p.rsi_upper or
                        self.sma1[ticker][0] < self.sma2[ticker][0]):
                        print(f"\t - Sell signal triggered for {data._name}")
                        self.orders[data._name] = self.close(data=data)
