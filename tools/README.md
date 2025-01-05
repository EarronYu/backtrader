# Backtrader Tools

This directory contains consolidated utilities and tools for working with the Backtrader framework. The tools are organized into three main categories:

## 1. Strategy Backtesting
Tools for running backtests with various trading strategies. These utilities simplify the process of:
- Loading and preprocessing data
- Configuring and running backtests
- Managing strategy parameters
- Analyzing backtest results

## 2. Strategy Parameter Optimization
Utilities for optimizing strategy parameters using Optuna:
- Define parameter search spaces
- Run optimization trials
- Track and analyze optimization results
- Find optimal parameter combinations

## 3. Report Generation
Tools for generating comprehensive strategy performance reports using Quantstats:
- Generate performance metrics
- Create visual analytics
- Export detailed HTML reports
- Compare strategy performance

## Usage
Each tool category has its own dedicated module:
- `backtest_runner.py` - For running strategy backtests
- `optimize.py` - For parameter optimization with Optuna
- `report.py` - For generating performance reports with Quantstats

Detailed usage instructions and examples will be provided in each module's documentation.
