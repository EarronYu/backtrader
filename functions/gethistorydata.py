import pandas as pd
import ccxt
import time
import os
import datetime

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行


def save_spot_candle_data_from_exchange(exchange, symbol, time_interval, start_time, path):
    """
    将某个交易所在指定日期指定交易对的K线数据，保存到指定文件夹
    :param exchange: ccxt交易所
    :param symbol: 指定交易对，例如'BTC/USDT'
    :param time_interval: K线的时间周期
    :param start_time: 指定日期，格式为'2020-03-16 00:00:00'
    :param path: 文件保存根目录
    :return:
    """
    # ===对火币的limit做特殊处理
    limit = None
    if exchange.id == 'huobipro':
        limit = 2000

    # ===开始抓取数据
    df_list = []
    start_time_since = exchange.parse8601(start_time)
    end_time = pd.to_datetime(start_time) + datetime.timedelta(days=1)

    while True:
        # 获取数据
        while True:
            try:
                df = exchange.fetch_ohlcv(symbol=symbol, timeframe=time_interval, since=start_time_since, limit=limit)
                break
            except:
                time.sleep(3)
        # 整理数据
        df = pd.DataFrame(df, dtype=float)  # 将数据转换为dataframe
        # 合并数据
        df_list.append(df)
        # 新的since
        t = pd.to_datetime(df.iloc[-1][0], unit='ms')
        start_time_since = exchange.parse8601(str(t))
        # 判断是否挑出循环
        if t >= end_time or df.shape[0] <= 1:
            break
        # 抓取间隔需要暂停2s，防止抓取过于频繁
        time.sleep(1.2)

    # ===合并整理数据
    df = pd.concat(df_list, ignore_index=True)
    # print(df)

    df.rename(columns={0: 'MTS', 1: 'open', 2: 'high',
                       3: 'low', 4: 'close', 5: 'volume'}, inplace=True)  # 重命名
    df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')  # 整理时间
    df = df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]  # 整理列的顺序

    # 选取数据时间段
    df = df[df['candle_begin_time'].dt.date == pd.to_datetime(start_time).date()]
    # 去重、排序
    df.drop_duplicates(subset=['candle_begin_time'], keep='last', inplace=True)
    df.sort_values('candle_begin_time', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # ===保存数据到文件
    # 创建交易所文件夹
    path = '../data/futures'
    if os.path.exists(path) is False:
        os.mkdir(path)
    # 创建日期文件夹
    path = os.path.join(path, str(pd.to_datetime(start_time).date()))
    if os.path.exists(path) is False:
        os.mkdir(path)
    # 拼接文件目录
    file_name = '_'.join([symbol.replace('/', ''), time_interval]) + '.csv'
    file_name = str(pd.to_datetime(start_time).date()) + '_' + file_name
    path = os.path.join(path, file_name)
    # 保存数据
    df.to_csv(path, index=False)


# 这下面是写入一些参数
begin_date = '2022-01-30'  # 手工设定开始时间
# end_date = begin_date  # 手工设定结束时间

end_date = '2023-01-25'  # 手工设定结束时间

date_list = []
date = pd.to_datetime(begin_date)
while date <= pd.to_datetime(end_date):
    date_list.append(str(date))
    date += datetime.timedelta(days=1)
    start_time = f'{begin_date} 00:00:00'

for start_time in date_list:
    # 如果历史数据抓完了那就把for缩进进去, 然后替换成为yesterday那个命令
    path = os.getcwd()
    print(path)
    error_list = []

    # 遍历交易所
    # for exchange in [ccxt.binance()]:
    # for exchange in [ccxt.binance({'timeout': 5000, 'enableRateLimit': False})]:
    for exchange in [ccxt.binance({'timeout': 5000, 'enableRateLimit': False,
                                   'proxies': {'https': 'http://127.0.0.1:7520', 'http': 'http://127.0.0.1:7520'}})]:
        # for exchange in [ccxt.huobipro(), ccxt.binance(), ccxt.okex()]:
        # 获取交易所需要的数据
        while True:
            try:
                market = exchange.load_markets()
                print('loaded')
                break
            except:
                time.sleep(3)

        market = pd.DataFrame(market).T

        symbol_list3 = list(market['symbol'])  # 获取所有交易对
        symbol_list1 = ['UNI/USDT', 'EGLD/USDT', 'BSV/USDT', 'XLM/USDT', 'KAVA/USDT', 'REN/USDT',
                        'DOGE/USDT', 'TRX/USDT', 'ONE/USDT', 'EOS/USDT', 'BTC/USDT', 'ADA/USDT',
                        'BNB/USDT', 'ETC/USDT', 'SUSHI/USDT', 'WAVES/USDT', '1INCH/USDT', 'ALGO/USDT',
                        'ATOM/USDT', 'XRP/USDT', 'XTZ/USDT', 'BTT/USDT', 'COMP/USDT', 'FTM/USDT',
                        'DOT/USDT', 'ETH/USDT', 'LTC/USDT', 'ZEC/USDT', 'RAY/USDT', 'SOL/USDT',
                        'RLC/USDT', 'XMR/USDT', 'LUNA/USDT', 'BCH/USDT', 'CRV/USDT', 'NEO/USDT',
                        'CHZ/USDT', 'SNX/USDT', 'LINK/USDT', 'AVAX/USDT', 'OMG/USDT', 'FIL/USDT',
                        'DASH/USDT', 'VET/USDT', 'AAVE/USDT', 'ICP/USDT']
        symbol_list2 = []
        # symbol_list = list(set(symbol_list2).union(set(symbol_list1)))
        # symbol_list = list(set(symbol_list3).difference(set(symbol_list1)))
        symbol_list = symbol_list3
        # print(symbol_list)
        # symbol_list = ["BTC/USDT"] # 只抓取目前主流币

        # 遍历交易对
        for symbol in symbol_list:
            if symbol.endswith('/USDT') is False:
                continue

            # 遍历时间周期
            for time_interval in ['1m']:
                print(exchange.id, symbol, time_interval)

                # 抓取数据并且保存
                try:
                    # 调用函数
                    save_spot_candle_data_from_exchange(exchange, symbol, time_interval, start_time, path)
                    print(start_time)
                except Exception as e:
                    print(e)
                    error_list.append('_'.join([exchange.id, symbol, time_interval]))

print(error_list)

