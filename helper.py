import pandas as pd
import glob
from tqdm import tqdm
from multiprocessing import Pool


def load_df(filename):
    asset = 'XBTU19'
    data = pd.read_csv(filename, header=0, low_memory=False, dtype={
                       'timestamp': str, 'symbol': str, 'bidPrice': float}, usecols=['timestamp', 'symbol', 'bidPrice'], skiprows=0, na_values=0)
    #print(data.columns, data[data.columns[1]])
    for n, i in enumerate(data['symbol']):
        if i == asset:
            data = pd.DataFrame(data.values[n:])
            #print (data)
            break
    for n, j in enumerate(data['symbol']):
        if j != asset:
            data = pd.DataFrame(data.values[:n])
            break
    print (data.head())
    #del data['symbol']
    return data


def load_dfs(asset, files):
    frm = files[0].split('/')[1].split('.')[0]
    too = files[-1].split('/')[1].split('.')[0]
    print('backtest dates: ' + frm + '-' + too)
    if 1 == 1 or not glob.glob('../loaded' + frm + too + '.csv'):
        a = []
        first = True
        for i in tqdm(files):
            data = load_df(filename=i)
            if not first:
                a = pd.concat([a, data], ignore_index=True)
            else:
                first = False
                a = data
        a.to_csv(path_or_buf='../loaded' + frm + too + '.csv', header=False)
    else:
        a = pd.read_csv('../loaded' + frm + too + '.csv', header=None,
                        low_memory=False, dtype={1: float}, usecols=[0, 1], skiprows=2, na_values=0)
    print('loaded ' + str(a.shape[0]) + ' ticks of data')
    return a


def load_dfs_mult(asset, files):
    # multiprocessing version of load_dfs
    frm = files[0].split('/')[1].split('.')[0]
    too = files[-1].split('/')[1].split('.')[0]

    files.reverse()
    print (files)
    print('backtest dates: ' + frm + '-' + too)
    if 1 == 1 or not glob.glob('../loaded' + frm + too + '.csv'):
        with Pool(processes=8) as pool:
            df_list = (pool.map(load_df, files))
            print(df_list)
            combined = pd.concat(df_list, ignore_index=True)
            print(combined)
            combined.to_csv(path_or_buf='../loaded' +
                            frm + too + '.csv', header=0)
    else:
        combined = pd.read_csv('../loaded' + frm + too + '.csv', header=None,
                               low_memory=False, dtype={1: float}, usecols=[0, 1], skiprows=2, na_values=0)
    print('loaded ' + str(combined.shape[0]) + ' ticks of data')
    return combined
