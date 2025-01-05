import warnings
from datetime import datetime
from datetime import timedelta
import optunity.metrics
import toolkit as tk
import pandas as pd
from PrepareCSV import prepare_data
from backtrader_plotting import Bokeh
import quantstats
import math
import backtrader as bt
from strategies.BBKCBreak import BBKCBreak


class CommInfoFractional(bt.CommissionInfo):
    def getsize(self, price, cash):
        '''Returns fractional size for cash operation @price'''
        return self.p.leverage * (cash / price)


class AllSizer(bt.Sizer):
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy is True:
            return math.floor(cash / data.high)
        if isbuy is False:
            return math.floor(cash / data.low)
        else:
            return self.broker.getposition(data)


class MyBuySell(bt.observers.BuySell):
    plotlines = dict(
        buy=dict(marker='^', markersize=4.0, color='lime', fillstyle='full'),
        sell=dict(marker='v', markersize=4.0, color='red', fillstyle='full')
        #
        # buy=dict(marker='$++$', markersize=12.0),
        # sell=dict(marker='$--$', markersize=12.0)
        #
        # buy=dict(marker='$✔$', markersize=12.0),
        # sell=dict(marker='$✘$', markersize=12.0)
    )


def runstrat(window, bbdevs, kcdevs, bias_pct, volatile_pct, stoploss):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(BBKCBreak, window=int(window), bbdevs=bbdevs, bias_pct=bias_pct, kcdevs=kcdevs,
                        volatile_pct=volatile_pct, stoploss=stoploss)
    dmoney0 = 1000.0
    cerebro.broker.setcash(dmoney0)
    # cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio', timeframe=bt.TimeFrame.Months, compression=3, factor=4)
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    # cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="TA")
    commission = 0.0004
    comminfo = CommInfoFractional(commission=commission)
    cerebro.broker.addcommissioninfo(comminfo)
    cerebro.addsizer(bt.sizers.FixedSize)
    tframes = dict(minutes=bt.TimeFrame.Minutes, days=bt.TimeFrame.Days, weeks=bt.TimeFrame.Weeks,
                   months=bt.TimeFrame.Months, years=bt.TimeFrame.Years)
    cerebro.resampledata(data, timeframe=tframes['minutes'], compression=1, name='Real')
    cerebro.resampledata(dataha, timeframe=tframes['minutes'], compression=1, name='Heikin')
    # cerebro.adddata(data)
    results = cerebro.run()
    # cerebro.plot()
    strat = results[0]
    anzs = strat.analyzers
    trade_info = anzs.TA.get_analysis()

    total_trade_num = trade_info["total"]["total"]
    if total_trade_num > 1:
        win_num = trade_info["won"]["total"]
        lost_num = trade_info["lost"]["total"]
        total_trades = total_trade_num
        winrate = win_num / total_trade_num
        lossrate = lost_num / total_trade_num
    else:
        total_trades, winrate, lossrate = 0, 0, 0
    #
    # warnings.filterwarnings('ignore')
    # portfolio_stats = strat.analyzers.getbyname('pyfolio')
    # returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
    # returns.index = returns.index.tz_convert(None)
    # dsharp = quantstats.stats.smart_sharpe(returns, periods=periods)
    # sortino = quantstats.stats.smart_sortino(returns, periods=periods)
    sqn = anzs.sqn.get_analysis().sqn
    dcash9 = cerebro.broker.getvalue()
    dcash0 = cerebro.broker.startingcash
    pnl = dcash9 / dcash0 - 1
    # if dsharp is not None:
    #     if (dsharp > 0) and (sqn > 1) and (sortino > 0) and (pnl > 0):
    #         param = sqn * dsharp * ((pnl + 1) ** 1/2) * ((sortino + 1) ** 1/2)
    #     else:
    #         param = 0
    # else:
    #     param = 0
    # return
    print(f'(交易次数={total_trades}, 胜率={winrate}, 分析指标 SQN={sqn}, pnl={pnl})')
    return sqn


"""84 days for backtest and 7 days for out sample test"""
symbol = 'ETHUSDT'
startdate = '2018-12-25'
enddate = '2021-12-01'
startingfund = 1000
# ----------------------
# prepare data
while startdate < enddate:
    t0str, t9str = startdate, (pd.to_datetime(startdate) + timedelta(days=6)).strftime('%Y-%m-%d')
    periods = (pd.to_datetime(t9str) - pd.to_datetime(t0str)).days
    print(t0str, t9str)
    data = tk.prepare_data(symbol=symbol, fromdt=t0str, todt=t9str, datapath=None)
    # print(df)
    # data = tk.pools_get4df(df, t0str, t9str, fgCov=fgCov)
    dataha = data.clone()
    dataha.addfilter(bt.filters.HeikinAshi(dataha))
    starttime = datetime.now()
    opt = optunity.maximize(runstrat, num_evals=80, solver_name='particle swarm', window=[1, 400], bbdevs=[0.01, 3.0],
                            kcdevs=[0.01, 3.0], bias_pct=[0.001, 0.15], volatile_pct=[0.001, 0.10],
                            stoploss=[0.02, 0.03])
    # long running
    endtime = datetime.now()
    duringtime = endtime - starttime
    print('time cost: ', duringtime)
    # 得到最优参数结果
    optimal_pars, details, _ = opt
    print('Optimal Parameters:')
    print('策略参数 window=%s, bbdevs=%s, kcdevs=%s, bias_pct=%s, volatile_pct=%s, stoploss=%s' % (
        optimal_pars['window'], optimal_pars['bbdevs'], optimal_pars['kcdevs'], optimal_pars['bias_pct'],
        optimal_pars['volatile_pct'], optimal_pars['stoploss']))
    # 利用最优参数最后回测一次，作图
    cerebro = bt.Cerebro()
    cerebro.addstrategy(BBKCBreak, window=int(optimal_pars['window']), bbdevs=optimal_pars['bbdevs'],
                        bias_pct=optimal_pars['bias_pct'], kcdevs=optimal_pars['kcdevs'],
                        volatile_pct=optimal_pars['volatile_pct'], stoploss=optimal_pars['stoploss'])

    dmoney0 = startingfund
    cerebro.broker.setcash(dmoney0)
    dcash0 = cerebro.broker.startingcash
    commission = 0.0004
    comminfo = CommInfoFractional(commission=commission)
    cerebro.broker.addcommissioninfo(comminfo)
    cerebro.addsizer(bt.sizers.FixedSize)
    t0test, t9test = (pd.to_datetime(t9str) + timedelta(days=1)).strftime('%Y-%m-%d'), (
            pd.to_datetime(t9str) + timedelta(weeks=1)).strftime('%Y-%m-%d')
    data = tk.prepare_data(symbol=symbol, fromdt=t0test, todt=t9test, datapath=None)

    dataha = data.clone()
    dataha.addfilter(bt.filters.HeikinAshi(dataha))
    tframes = dict(minutes=bt.TimeFrame.Minutes, days=bt.TimeFrame.Days, weeks=bt.TimeFrame.Weeks,
                   months=bt.TimeFrame.Months, years=bt.TimeFrame.Years)
    cerebro.resampledata(data, timeframe=tframes['minutes'], compression=1, name='Real')
    cerebro.resampledata(dataha, timeframe=tframes['minutes'], compression=1, name='Heikin')
    # bt.observers.BuySell = MyBuySell

    # 设置pyfolio分析参数
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    #
    print('\n\t#运行cerebro')
    results = cerebro.run(maxcpus=True)
    # results = cerebro.run(runonce=False, exactbars=-2)
    print('\n#基本BT量化分析数据')
    dval9 = cerebro.broker.getvalue()
    kret = (dval9 - dcash0) / dcash0 * 100
    # 最终投资组合价值
    strat = results[0]
    print('\t起始资金 Starting Portfolio Value: %.2f' % dcash0)
    print('\t资产总值 Final Portfolio Value: %.2f' % dval9)
    print('\tROI投资回报率 Return on investment: %.2f %%' % kret)
    warnings.filterwarnings('ignore')
    portfolio_stats = strat.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()

    returns.index = returns.index.tz_convert(None)
    returns.to_csv(f'..//data//returns//returns_{t0test}-{t9test}.csv')
    # quantstats.reports.html(returns, output=f'..//data//optstats_{t0test}-{t9test}.html', title=f'Crypto Sentiment {t0test}-{t9test}')
    # cerebro.plot()

    dmoney0 = dval9
    t0str = (pd.to_datetime(t0str) + timedelta(weeks=1)).strftime('%Y-%m-%d')
    startdate = t0str

import os


def as_num(x):
    y = '{:.10f}'.format(x)  # .10f 保留10位小数
    return y


### 读取文件中的数据内容。
warnings.filterwarnings('ignore')
symbol = 'ETHUSDT'
os.listdir(u"../data/returns//")
Folder_Path = u"../data/returns//"  # 要拼接的文件夹及其完整路径，注意不要包含中文
SaveFile_Path = u"../data//results"  # 拼接后要保存的文件路径
SaveFile_Name = u'returns.csv'  # 合并后要保存的文件名
# 将该文件夹下的所有文件名存入一个列表
file_list = os.listdir(u"../data/returns//")

# 读取第一个CSV文件并包含表头
df = pd.read_csv(Folder_Path + '\\' + file_list[0], skipfooter=1, engine='python')  # 编码默认UTF-8，若乱码自行更改
# 将读取的第一个CSV文件写入合并后的文件保存
df.to_csv(SaveFile_Path + '\\' + SaveFile_Name, index=False)

# 循环遍历列表中各个CSV文件名，并追加到合并后的文件
for i in range(1, len(file_list)):
    df = pd.read_csv(Folder_Path + '\\' + file_list[i], skipfooter=1, engine='python')
    df.to_csv(SaveFile_Path + '\\' + SaveFile_Name, index=False, header=False, mode='a+')

# # 读取全部是数据
returns = pd.read_csv(u"../data/results/returns.csv", index_col='index')
# returns.set_index(returns['index'], inplace=True, drop=True)
returns.index = pd.DatetimeIndex(returns.index)
# returns.index = returns.index.tz_convert(None)
for i in returns.index:
    if 'E' in str(returns.loc[i, 'return']) or 'e' in str(returns.loc[i, 'return']):
        x = as_num(float(returns.loc[i, 'return']))
        returns.loc[i, 'return'] = float(x)

t0str = (returns.index[0]).strftime('%Y-%m-%d')
t9str = (returns.index[-1]).strftime('%Y-%m-%d')
data = tk.prepare_data(symbol, t0str, t9str)
benchmark = pd.read_csv(f'..//data//{symbol}_{t0str}_{t9str}_1m.csv', index_col='datetime')
benchmark.index = pd.DatetimeIndex(benchmark.index)
period_type = 'D'
benchmark = benchmark.resample(period_type).last()
benchmark["prevClose"] = benchmark['close'].shift(1)
benchmark['change'] = benchmark[['close', 'prevClose']].pct_change(axis=1)['prevClose']
quantstats.reports.html(returns=returns['return'], output=f'..//data//results//{symbol}_optstats.html',
                        periods_per_year=365, title='Crypto Sentiment', benchmark=benchmark['change'])
