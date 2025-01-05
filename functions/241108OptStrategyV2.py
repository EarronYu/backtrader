import math
import warnings
from datetime import datetime

import backtrader as bt
import gradient_free_optimizers as gfo
import numpy as np
import quantstats
from strategies.BollingerKeltnerChannel import MyStrategy

import toolkit as tk
from PrepareCSV import prepare_data
import warnings

warnings.filterwarnings('ignore')


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
    )


# ----------------------
# prepare data
t0str, t9str = '2020-01-01', '2021-01-01'
symbol = 'ETHUSDT'
fgCov = False
df = prepare_data(t0str, t9str, symbol, fgCov=fgCov, prep_new=True, mode='opt')
data = tk.pools_get4df(df, t0str, t9str, fgCov=fgCov)

dmoney0 = 1000.0
commission = 0.0004
timescale = "minutes"
timecompression = 5


def runstrat(para):
    cerebro = bt.Cerebro()
    data = tk.prepare_data(symbol=symbol, fromdt=t0str, todt=t9str, datapath=None)
    for key in ["var1", "var2", "var3", "var4"]:
        para[key] = float(para[key])
    cerebro.addstrategy(MyStrategy, window=int(para["var1"]), bbdevs=para["var2"],
                        kcdevs=para["var3"], bias_pct=para["var4"])
    cerebro.broker.setcash(dmoney0)
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    comminfo = CommInfoFractional(commission=commission)
    cerebro.broker.addcommissioninfo(comminfo)
    cerebro.addsizer(bt.sizers.SizerFix)
    tframes = dict(minutes=bt.TimeFrame.Minutes, days=bt.TimeFrame.Days, weeks=bt.TimeFrame.Weeks,
                   months=bt.TimeFrame.Months, years=bt.TimeFrame.Years)
    cerebro.resampledata(data, timeframe=tframes[timescale], compression=timecompression, name='Real')
    # cerebro.resampledata(dataha, timeframe=tframes['minutes'], compression=1, name='Heikin')
    # cerebro.adddata(data)
    results = cerebro.run()
    strat = results[0]
    anzs = strat.analyzers
    #
    warnings.filterwarnings('ignore')
    portfolio_stats = strat.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
    returns.index = returns.index.tz_convert(None)
    dsharp = quantstats.stats.smart_sharpe(returns, periods=365)

    sortino = quantstats.stats.adjusted_sortino(returns, periods=365, smart=True)
    exposure = quantstats.stats.exposure(returns)

    sqn = anzs.sqn.get_analysis().sqn
    dcash9 = cerebro.broker.getvalue()
    dcash0 = cerebro.broker.startingcash
    pnl = (dcash9 / dcash0 - 1) * 100
    if dsharp is not None and sortino is not None:
        if (dsharp > 1) and (sqn > 1) and (sortino > 1) and (pnl > 0):
            param = sqn + dsharp + sortino + (exposure*10)**0.5
            print(f"{pnl}%")
        else:
            param = sqn + dsharp + sortino + (exposure*10)**0.5


    else:
        param = 0
    return param


print("开始优化")
starttime = datetime.now()
# 参数搜索空间
# window=int(para["var1"]), bbdevs=int(para["var2"]),
#                         kcdevs=para["var3"], bias_pct=para["var4"]
search_space = {
    "var1": np.arange(1, 75, 1),
    "var2": np.arange(0, 5, 0.1),
    "var3": np.arange(0, 5, 0.1),
    "var4": np.arange(0, 0.1, 0.01)
}
# 迭代次数
iterations = 200
# 可以使用的优化器
# 'HillClimbingOptimizer'
# "RepulsingHillClimbingOptimizer'
# 'simulatedAnnealingOptimizer'
# 'RandomSearchOptimizer'.
# RandomRestartHillClimbingOptimizer'
# 'RandomAnnealingOptimizer'
# 'ParallelTemperingOptimizer'.
# 'ParticleSwarmOptimizer',
# 'EvolutionStrategyOptimizer'
# 'DecisionTreeOptimizer'
# 创建优化器
# opt = gfo.ParticleSwarmOptimizer(search_space)
opt = gfo.EvolutionStrategyOptimizer(search_space)
# 执行搜索，参数是目标函数和迭代次数，其它参数请参考函数源码
opt.search(runstrat, n_iter=iterations)

# 优化完成，得到最优参数结果

print('window=var1: ', opt.best_para['var1'])
print('bbdevs=var2: ', opt.best_para['var2'])
print('kcdevs=var3: ', opt.best_para['var3'])
print('bias_pct=var4: ', opt.best_para['var4'])
# long-running
endtime = datetime.now()
duringtime = endtime - starttime
print('time cost: ', duringtime)
print('\n#优化成功')
# 利用最优参数最后回测一次，作图
cerebro = bt.Cerebro()
for key in ["var1", "var2", "var3", "var4"]:
    opt.best_para[key] = float(opt.best_para[key])
cerebro.addstrategy(MyStrategy, window=int(opt.best_para['var1']), bbdevs=opt.best_para['var2'],
                    kcdevs=opt.best_para['var3'], bias_pct=opt.best_para['var4'])

cerebro.broker.setcash(dmoney0)
dcash0 = cerebro.broker.startingcash
comminfo = CommInfoFractional(commission=commission)
cerebro.broker.addcommissioninfo(comminfo)
cerebro.addsizer(bt.sizers.SizerFix)
tframes = dict(minutes=bt.TimeFrame.Minutes, days=bt.TimeFrame.Days, weeks=bt.TimeFrame.Weeks,
               months=bt.TimeFrame.Months, years=bt.TimeFrame.Years)
cerebro.resampledata(data, timeframe=tframes[timescale], compression=timecompression, name='Real')
# cerebro.resampledata(dataha, timeframe=tframes['minutes'], compression=10, name='Heikin')
bt.observers.BuySell = MyBuySell

# 设置pyfolio分析参数
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
#
print('\n\t#运行cerebro')
results = cerebro.run(maxcpus=True)
# results = cerebro.run(runonce=False, exactbars=-2)
print('\n#基本BT量化分析数据')
dval9 = cerebro.broker.getvalue()
dget = dval9 - dcash0
kret = dget / dcash0 * 100
# 最终投资组合价值
strat = results[0]
print('\t起始资金 Starting Portfolio Value: %.2f' % dcash0)
print('\t资产总值 Final Portfolio Value: %.2f' % dval9)
print('\t利润总额:  %.2f,' % dget)
print('\tROI投资回报率 Return on investment: %.2f %%' % kret)

print('\n==================================================')
print('\n quantstats专业量化分析图表\n')
warnings.filterwarnings('ignore')
portfolio_stats = strat.analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
returns.index = returns.index.tz_convert(None)
print(returns)
quantstats.reports.html(returns, output='..//data//optstats.html', title='Crypto Sentiment')
print('\n#回测完成')
#
# print('\n#绘制BT量化分析图形')
# try:
#     b = Bokeh(plot_mode='single', output_mode='save', filename='..//data//optreport.html')
#     cerebro.plot(b)
# except:
#     cerebro.plot()

#
#
