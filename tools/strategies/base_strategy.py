import backtrader as bt
import logging

class BaseStrategy(bt.Strategy):
    """
    Base strategy class with common functionality for all strategies
    """
    params = (
        ('verbose', True),  # Enable logging of trades
    )

    def __init__(self):
        super().__init__()
        self.order = None  # Keep track of pending orders
        self.trades = []   # Keep track of completed trades

    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                if self.p.verbose:
                    logging.info(
                        f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, '
                        f'Comm: {order.executed.comm:.2f}'
                    )
            else:
                if self.p.verbose:
                    logging.info(
                        f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, '
                        f'Comm: {order.executed.comm:.2f}'
                    )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if self.p.verbose:
                logging.warning('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        """Handle trade notifications"""
        if trade.isclosed:
            self.trades.append(trade)
            if self.p.verbose:
                logging.info(
                    f'TRADE PROFIT, GROSS: {trade.pnl:.2f}, '
                    f'NET: {trade.pnlcomm:.2f}'
                )

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        if self.p.verbose:
            logging.info(f'{dt.isoformat()}, {txt}')
