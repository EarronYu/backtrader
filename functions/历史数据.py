import pandas as pd
import ccxt
import time
import os
from datetime import timedelta
from sys import exit
pd.set_option('expand_frame_repr', False)
# pd.set_option('display.max_rows', None)
# 设定参数
exchange = ccxt.binance({
    'timeout': 5000,
    'enableRateLimit': True,
    'proxies': {'https': 'http://127.0.0.1:7890', 'http': 'http://127.0.0.1:7890'}
})

symbol_list = ['MATIC/USDT', 'RLC/USDT', 'BTC/USDT', 'BCH/USDT', 'ZEC/USDT', 'DASH/USDT', 'DOGE/USDT', 'LTC/USDT', 'XMR/USDT', 'XRP/USDT', 'XLM/USDT', 'ALGO/USDT', 'ADA/USDT', 'SOL/USDT', 'LUNA/USDT', 'VET/USDT', 'EGLD/USDT', 'ICP/USDT', 'AVAX/USDT', 'ATOM/USDT', 'EOS/USDT', 'ETH/USDT', 'ETC/USDT', 'DOT/USDT', 'OMG/USDT', 'FTM/USDT', 'ONE/USDT', 'NEO/USDT', 'XTZ/USDT', 'TRX/USDT', 'WAVES/USDT', 'BNB/USDT', 'SUSHI/USDT', 'COMP/USDT', 'CRV/USDT', 'SNX/USDT', 'KAVA/USDT', 'LINK/USDT', 'FIL/USDT', 'ZEC/USDT', 'UNI/USDT', 'AAVE/USDT', 'SUSHI/USDT', 'RAY/USDT', 'REN/USDT', '1INCH/USDT']


def main():
    for symbol in symbol_list:
        if symbol.endswith('/USDT') is False:
            continue
    for time_interval in ['5m']:
        print(exchange.id, symbol, time_interval)
    time_interval = '1m'  # 抓取数据的时间跨度

    temp = pd.read_hdf('BTC-USDT_5m.h5', key='df', mode='r').copy().tail(1)
    temp.reset_index(drop=True, inplace=True)
    temp = temp.T
    temp.reset_index(drop=True, inplace=True)
    new_start_time = temp.at[0, 0]
    new_start_time = "'%s'" % new_start_time
    # 抓取数据开始结束时间
    start_time = new_start_time
    _start_time = start_time
    # print(start_time)
    # exit()
    end_time = pd.to_datetime(start_time) + timedelta(days=1)
    # print(end_time)
    # exit()
    _ = end_time.to_pydatetime()
    _ = int(time.time() // 60 * 60 * 1000)
    # print(_)
    # exit()
    # # 转换成localtime
    _ = time.localtime(_ / 1000)
    # # 转换成新的时间格式(2016-05-05 20:28:54)
    _end_time = time.strftime("%Y-%m-%d %H:%M:%S", _)
    # print(_end_time)
    # exit()
    temp_start_time = temp.at[0, 0]
    temp_start_time = int(time.time() // 60 * 60 * 1000)  # timestamp to int
    temp_start_time = time.localtime(temp_start_time / 1000)  # 转换成localtime
    temp_start_time = time.strftime("%Y-%m-%d %H:%M:%S", _)

    print('-' * 25)
    print('|' + '    |' + '      时间区间')
    print('|' + '    |' + temp_start_time)
    print('V' + '    |' + _end_time)
    print('-' * 25)
    start_time_since = exchange.parse8601(start_time)
    df = exchange.fetch_ohlcv(symbol=symbol, timeframe=time_interval, since=start_time_since)
    df = pd.DataFrame(df, dtype=float)  # 将数据转换为dataframe
    df['candle_begin_time'] = pd.to_datetime(df[0], unit='ms')  # 整理时间
    _ = df.copy()
    print(_)

    # 开始循环抓取数据
    df_list = []
    start_time_since = exchange.parse8601(start_time)
    # end_time = pd.to_datetime(start_time) + timedelta(days=1)
    while True:
        # 获取数据
        df = exchange.fetch_ohlcv(symbol=symbol, timeframe=time_interval, since=start_time_since)

        # 整理数据
        df = pd.DataFrame(df, dtype=float)  # 将数据转换为dataframe
        df['candle_begin_time'] = pd.to_datetime(df[0], unit='ms')
        # print(df)

        # 合并数据
        df_list.append(df)

        # 指明新的since
        t = pd.to_datetime(df.iloc[-1][0], unit='ms')
        # print(t)
        start_time_since = exchange.parse8601(str(t))

        # 判断是否跳出循环
        if t >= end_time or df.shape[0] <= 1:
            print('抓取完所需数据,退出循环')
            break

        # 抓取间隔需要暂停两秒,防止抓取过于频繁
        time.sleep(1)

    # ====合并整理数据
    df = pd.concat(df_list, ignore_index=True)

    df.rename(columns={0: 'MTS', 1: 'open', 2: 'high',
                       3: 'low', 4: 'close', 5: 'volume'}, inplace=True)
    df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')
    df = df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]
    # 存储到hdf
    df.to_hdf('historyK.h5', key='df', mode='w')
    # 选取时间段
    df = df[df['candle_begin_time'].dt.date == pd.to_datetime(start_time).date()]

    # 去重/排序
    df.drop_duplicates(subset=['candle_begin_time'], keep='last', inplace=True)
    df.sort_values('candle_begin_time', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 保存数据到文件

    # 根目录,确保路径存在
    # path = r'E:\BaiduNetdiskDownload\量化交易\xbx-coin-2020_part2\data\history_candle_data'
    # path = os.path.join(path, exchange.id)
    # print(path)
    # if os.path.exists(path) is False:
    #     os.mkdir(path)
    # # 创建spot文件夹
    # path = os.path.join(path, 'spot')
    # if os.path.exists(path) is False:
    #     os.mkdir(path)
    # # 创建日期文件夹
    # path = os.path.join(path, str(pd.to_datetime(start_time).date()))
    # if os.path.exists(path) is False:
    #     os.mkdir(path)
    # # 拼接文件目录
    # file_name = '_'.join([symbol.replace('/', '-'), time_interval]) + '.csv'
    # path = os.path.join(path, file_name)
    # print(path)
    #
    # df.to_csv(path, index=False)
    df_list2 = []  # 设定空表格df_list2
    df1 = pd.read_hdf('BTC-USDT_5m.h5', key='df')  # 将historyK放入df1
    df2 = pd.read_hdf('historyK.h5', key='df')  # 将BTC-USDT_5m放入df2
    df_list2 = df1.append(df2, ignore_index=True, sort=True)  # 将df1和df2的组合放入df_list2
    # print(df_list2)

    df3 = pd.concat([df1, df2], ignore_index=True)  # concat产生一个新的数组,后面操作不会影响原数组
    df = pd.DataFrame(df3)
    # df['candle_begin_time'] = pd.to_datetime(df3[0], unit='ms')  # 整理时间
    df.rename(columns={0: 'MTS', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'}, inplace=True)  # 重新设定index
    df['candle_begin_time'] = pd.to_datetime(df['candle_begin_time'], unit='ms')  # 将candle_begin_time作为时间变量
    df = df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]  # 只输出部分列表
    df.drop_duplicates(subset=['candle_begin_time'], keep='last', inplace=True)  # 删除拼接重复的candle_begin_time
    df.sort_values('candle_begin_time', inplace=True)  # 以candle_begin_time来排列数据
    df.reset_index(drop=True, inplace=True)

    print(df)
    df.to_hdf('BTC-USDT_5m.h5', key='df', mode='w')

    df.to_csv('BTC-USDT_5m.csv', index=False)
    print('k线数据已更新')

    time.sleep(1)

if __name__ == '__main__':
    while True:
        main()
        time.sleep(2)
else:
    print('已经抓取所有历史数据')
#


