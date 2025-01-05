import os
import pandas as pd
import quantstats
import toolkit as tk
import warnings

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
    # print(i, returns.loc[i, 'return'], (returns.loc[i, 'return']).dtype)
# print(returns.loc['2018-04-16', 'return'])
# print(returns)
# print(returns['return'].dtypes)
# all_date.to_csv(u"F:/公司/03_Study/01_爬虫/source_data.csv")
# quantstats.reports.full(returns['return'], periods_per_year=365)
# quantstats.reports.full(returns['return'], periods_per_year=365, )
# print(returns.index[1])
# print(returns.index[-1])
t0str = (returns.index[0]).strftime('%Y-%m-%d')
t9str = (returns.index[-1]).strftime('%Y-%m-%d')
data = tk.prepare_data(symbol, t0str, t9str)
benchmark = pd.read_csv(f'..//data//{symbol}_{t0str}_{t9str}_1m.csv', index_col='datetime')
benchmark.index = pd.DatetimeIndex(benchmark.index)
period_type = 'D'
benchmark = benchmark.resample(period_type).last()
benchmark["prevClose"] = benchmark['close'].shift(1)
benchmark['change'] = benchmark[['close', 'prevClose']].pct_change(axis=1)['prevClose']
# print(benchmark['change'])
quantstats.reports.html(returns=returns['return'], output=f'..//data//results//{symbol}_optstats.html', periods_per_year=365, title='Crypto Sentiment', benchmark=benchmark['change'])
