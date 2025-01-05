#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                      unicode_literals)

import datetime as dt
import os
import logging
import pytz
from typing import Type, Dict, Any, Optional, Union

import backtrader as bt
from backtrader import TimeFrame
from backtrader.feeds import GenericCSVData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Time period mapping
TIMEFRAME_MAP = {
    '1m': (TimeFrame.Minutes, 1),
    '5m': (TimeFrame.Minutes, 5),
    '15m': (TimeFrame.Minutes, 15),
    '30m': (TimeFrame.Minutes, 30),
    '1h': (TimeFrame.Minutes, 60),
    '4h': (TimeFrame.Minutes, 240),
    '1d': (TimeFrame.Days, 1),
}


def run_backtest(
    strategy_cls: Type[bt.Strategy],
    data_path: Optional[str] = None,
    start_date: Optional[Union[dt.datetime, str]] = None,
    end_date: Optional[Union[dt.datetime, str]] = None,
    timeframe: str = '1m',
    compression: int = 1,
    cash: float = 100000.0,
    commission: float = 0.001,
    verbose: bool = True,
    params: Optional[Dict[str, Any]] = None,
) -> bt.Strategy:
    """
    Run a backtest for a given strategy and data.

    Args:
        strategy_cls: The strategy class to backtest
        data_path: Path to the data file (CSV format)
        params: Strategy parameters
        fromdate: Start date for the backtest (datetime or 'YYYY-MM-DD' string)
        todate: End date for the backtest (datetime or 'YYYY-MM-DD' string)
        cash: Initial cash amount
        commission: Commission rate (e.g., 0.001 for 0.1%)
        verbose: Whether to print progress information

    Returns:
        The strategy instance after running the backtest

    Raises:
        ValueError: If the data file doesn't exist or dates are invalid
        TypeError: If strategy_cls is not a subclass of bt.Strategy
    """
    # Validate inputs
    if not issubclass(strategy_cls, bt.Strategy):
        raise TypeError("strategy_cls must be a subclass of bt.Strategy")
    
    if data_path is None:
        raise ValueError("data_path must be provided")
    if not os.path.exists(data_path):
        raise ValueError(f"Data file not found: {data_path}")

    """
    Run a backtest for a given strategy and data.

    Args:
        strategy_cls: The strategy class to backtest
        data_path: Path to the data file (CSV format)
        params: Strategy parameters
        fromdate: Start date for the backtest (datetime or 'YYYY-MM-DD' string)
        todate: End date for the backtest (datetime or 'YYYY-MM-DD' string)
        cash: Initial cash amount
        commission: Commission rate (e.g., 0.001 for 0.1%)

    Returns:
        The strategy instance after running the backtest
    """
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    if verbose:
        logging.info(f"Initializing backtest for {strategy_cls.__name__}")

    # Set the initial cash
    cerebro.broker.setcash(cash)

    # Set the commission
    cerebro.broker.setcommission(commission=commission)

    # Process dates
    fromdate = None
    todate = None
    
    if start_date is not None:
        if isinstance(start_date, str):
            try:
                fromdate = dt.datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                fromdate = dt.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
            fromdate = fromdate.replace(tzinfo=pytz.UTC)
        else:
            fromdate = start_date
    
    if end_date is not None:
        if isinstance(end_date, str):
            try:
                todate = dt.datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                todate = dt.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
            todate = todate.replace(tzinfo=pytz.UTC)
        else:
            todate = end_date

    # If no start date provided, use 30 days ago
    if fromdate is None:
        fromdate = dt.datetime.now(pytz.UTC) - dt.timedelta(days=30)
    
    # If no end date provided, use current time
    if todate is None:
        todate = dt.datetime.now(pytz.UTC)

    # Parse timeframe
    tf, comp = TIMEFRAME_MAP.get(timeframe, (TimeFrame.Minutes, 1))
    comp *= compression  # Apply compression factor

    # Create a custom data feed for the specific CSV format
    class BinanceCSVData(GenericCSVData):
        """Custom CSV Data feed for Binance format"""
        params = (
            ('nullvalue', float('NaN')),
            ('dtformat', '%Y-%m-%d %H:%M:%S'),
            ('datetime', 0),
            ('open', 1),
            ('high', 2),
            ('low', 3),
            ('close', 4),
            ('volume', 5),
            ('openinterest', -1),
            ('headers', True),  # CSV file has headers
        )

    # Add the data
    data = BinanceCSVData(
        dataname=data_path,
        fromdate=fromdate,
        todate=todate,
        timeframe=tf,
        compression=comp
    )
    cerebro.adddata(data)

    # Add the strategy
    if params is None:
        params = {}
    cerebro.addstrategy(strategy_cls, **params)

    # Run the backtest
    if verbose:
        logging.info("Starting backtest...")
        
    results = cerebro.run()
    
    if verbose:
        final_value = results[0].broker.getvalue()
        returns = (final_value - cash) / cash * 100
        logging.info(f"Backtest completed. Final value: ${final_value:.2f} (Return: {returns:.2f}%)")

    # Return the first strategy instance
    return results[0]


def print_backtest_results(strategy: bt.Strategy) -> None:
    """
    Print the results of a backtest.

    Args:
        strategy: The strategy instance after running a backtest
    """
    portfolio_value = strategy.broker.getvalue()
    print('Final Portfolio Value: %.2f' % portfolio_value)

    # If the strategy has a trades list, print trade statistics
    if hasattr(strategy, 'trades'):
        total_trades = len(strategy.trades)
        if total_trades > 0:
            winning_trades = sum(1 for trade in strategy.trades if trade.pnl > 0)
            losing_trades = sum(1 for trade in strategy.trades if trade.pnl < 0)
            win_rate = (winning_trades / total_trades) * 100

            print('Number of Trades: %d' % total_trades)
            print('Winning Trades: %d' % winning_trades)
            print('Losing Trades: %d' % losing_trades)
            print('Win Rate: %.2f%%' % win_rate)


if __name__ == '__main__':
    # Example usage
    class ExampleStrategy(bt.Strategy):
        """
        Example strategy using SMA crossover for demonstration.
        Adapted from the optimization example with proper parameter handling.
        """
        params = dict(
            period=20,  # SMA period
            verbose=True,  # Enable logging of trades
        )

        def __init__(self):
            # Initialize parent class first
            super().__init__()
            # Create SMA indicator
            self.sma = bt.ind.SMA(self.data0, period=self.p.period)
            # Keep track of trades for analysis
            self.trades = []
            
            # For convenience, keep track of open position
            self.order = None

        def next(self):
            # Skip if we have a pending order
            if self.order:
                return

            # Check if we are in the market
            if not self.position:
                # Buy if price crosses above SMA
                if self.data.close[0] > self.sma[0]:
                    self.order = self.buy()
                    if self.order and self.p.verbose:
                        logging.info(f'BUY CREATE {self.data.close[0]:.2f}')
            else:
                # Sell if price crosses below SMA
                if self.data.close[0] < self.sma[0]:
                    self.order = self.sell()
                    if self.order and self.p.verbose:
                        logging.info(f'SELL CREATE {self.data.close[0]:.2f}')

        def notify_order(self, order):
            if order.status in [order.Submitted, order.Accepted]:
                # Order submitted/accepted - nothing to do
                return

            # Check if an order has been completed
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

            # Reset order
            self.order = None

        def notify_trade(self, trade):
            if trade.isclosed:
                self.trades.append(trade)
                if self.p.verbose:
                    logging.info(
                        f'TRADE PROFIT, GROSS: {trade.pnl:.2f}, '
                        f'NET: {trade.pnlcomm:.2f}'
                    )

    # Run example backtest
    strategy = run_backtest(
        strategy_cls=ExampleStrategy,
        data_path='path/to/your/data.csv',
        params={'period': 20},
        start_date='2020-01-01',
        end_date='2023-12-31'
    )
    print_backtest_results(strategy)
