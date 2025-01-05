from datetime import datetime
import os

import pandas as pd


def file_list(dirname, ext='.csv'):
    """获取目录下所有特定后缀的文件
    @param dirname: str 目录的完整路径
    @param ext: str 后缀名, 以点号开头
    @return: list(str) 所有子文件名(不包含路径)组成的列表
    """
    return list(filter(
        lambda filename: os.path.splitext(filename)[1] == ext,
        os.listdir(dirname)))


def all_path(dirname):
    # filelistlog = dirname + "\\filelistlog.txt"  # 保存文件路径
    nlist = []
    postfix = {'csv'}  # 设置要保存的文件格式
    for maindir, subdir, file_name_list in os.walk(dirname):
        for filename in file_name_list:
            apath = os.path.join(filename)
            # if True:        # 保存全部文件名。若要保留指定文件格式的文件名则注释该句
            if apath.split('.')[-1] in postfix:  # 匹配后缀，只保存所选的文件格式。若要保存全部文件，则注释该句
                try:
                    nlist.append(apath)
                    # with open(filelistlog, 'a+') as fo:
                    #     fo.writelines(apath)
                    #     fo.write('\n')
                except:
                    pass  # 所有异常全部忽略即可
    return nlist


# symbol_list1 = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'XRP/USDT',
#                 'UNI/USDT', 'LTC/USDT', 'LINK/USDT', 'BCH/USDT', 'XLM/USDT', 'LUNA/USDT',
#                 'DOGE/USDT', 'VET/USDT', 'FIL/USDT', 'AAVE/USDT',
#                 'ATOM/USDT', 'AVAX/USDT', 'TRX/USDT', 'XMR/USDT', 'EOS/USDT', 'BTT/USDT',
#                 'CHZ/USDT', 'BSV/USDT']
# symbol_list2 = ['RLC/USDT', 'BTC/USDT', 'BCH/USDT', 'ZEC/USDT', 'DASH/USDT', 'DOGE/USDT',
#                 'LTC/USDT', 'XMR/USDT', 'XRP/USDT', 'XLM/USDT', 'ALGO/USDT', 'ADA/USDT',
#                 'SOL/USDT', 'LUNA/USDT', 'VET/USDT', 'EGLD/USDT', 'ICP/USDT', 'AVAX/USDT',
#                 'ATOM/USDT', 'EOS/USDT', 'ETH/USDT', 'ETC/USDT', 'DOT/USDT', 'OMG/USDT',
#                 'FTM/USDT', 'ONE/USDT', 'NEO/USDT', 'XTZ/USDT', 'TRX/USDT', 'WAVES/USDT',
#                 'BNB/USDT', 'SUSHI/USDT', 'COMP/USDT', 'CRV/USDT', 'SNX/USDT', 'KAVA/USDT',
#                 'LINK/USDT', 'FIL/USDT', 'ZEC/USDT', 'UNI/USDT', 'AAVE/USDT', 'SUSHI/USDT',
#                 'RAY/USDT', 'REN/USDT', '1INCH/USDT']
# 临时给symbol_list求并集
symbol_list = ['UNI/USDT', 'EGLD/USDT', 'BSV/USDT', 'XLM/USDT', 'KAVA/USDT', 'REN/USDT',
               'DOGE/USDT', 'TRX/USDT', 'ONE/USDT', 'EOS/USDT', 'BTC/USDT', 'ADA/USDT',
               'BNB/USDT', 'ETC/USDT', 'SUSHI/USDT', 'WAVES/USDT', '1INCH/USDT', 'ALGO/USDT',
               'ATOM/USDT', 'XRP/USDT', 'XTZ/USDT', 'BTT/USDT', 'COMP/USDT', 'FTM/USDT',
               'DOT/USDT', 'ETH/USDT', 'LTC/USDT', 'ZEC/USDT', 'RAY/USDT', 'SOL/USDT',
               'RLC/USDT', 'XMR/USDT', 'LUNA/USDT', 'BCH/USDT', 'CRV/USDT', 'NEO/USDT',
               'CHZ/USDT', 'SNX/USDT', 'LINK/USDT', 'AVAX/USDT', 'OMG/USDT', 'FIL/USDT',
               'DASH/USDT', 'VET/USDT', 'AAVE/USDT', 'ICP/USDT']
print(symbol_list)
# 需要处理的csv文件路径
# absolute path 绝对路径
dirname = 'D://BaiduNetdiskDownload//Quants//Data///binance//sot_by_datetime//'
dtsbl = all_path(dirname)
# print(dtsbl)
# 需要处理的时间表
dt = os.listdir(dirname)
print(dt)
# 创建dataframe
df = pd.DataFrame(data=0, columns=symbol_list, index=dt, dtype=int)
# 首先将所有数据文件命名为统一格式
dname0 = 'D://BaiduNetdiskDownload//Quants//Data///binance//sot_by_datetime//'
dt0 = os.listdir(dname0)
for d in dt0:
    curpath = dname0 + d + '//'
    fnamelist0 = os.listdir(curpath)
    for fname0 in fnamelist0:
        dt1 = fname0[0:10]
        if dt1 not in dt0:
            ofn = dname0 + d + '//' + fname0
            nfname0 = fname0.replace('-', '')
            nfn = dname0 + d + '//' + d + '_' + nfname0
            try:
                os.rename(ofn, nfn)
            except:
                print(f'问题出在: {d}//{fname0} 上面')

# 将每个时间下的symbol记录下来
for x in dtsbl:
    dt0 = x[0:10]
    # print(dt0)
    symbol = x[11:-7]
    # print(symbol)
    symbol = symbol.replace('USDT', '/USDT')
    # print(symbol)
    df.loc[dt0, symbol] = 1
print(df)


def color_negative_red(val):
    color = 'red' if val == 0 else 'black'
    return 'color: %s' % color


df.style.applymap(color_negative_red)
df.to_excel('errors.xls')