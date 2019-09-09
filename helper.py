import pandas as pd
import glob


def load_df(asset, filename):
    data = pd.read_csv(filename, header=None, low_memory=False, dtype={
                       3: float}, usecols=[0, 1, 3], skiprows=2)

    for n, i in enumerate(data[1]):
        if i == asset:
            data = pd.DataFrame(data.values[n:])
            break

    for n, j in enumerate(data[1]):
        if j != asset:
            data = pd.DataFrame(data.values[:n])
            break

    del data[0]
    del data[1]
    return data


def load_dfs(asset, files):
    frm = files[0].split('/')[1].split('.')[0]
    too = files[-1].split('/')[1].split('.')[0]
    print('backtest dates: ' + frm + '-' + too)
    if not glob.glob('../'+frm+too+'.csv'):
        a = []
        first = True
        for i in files:
            data = load_df(asset, filename=i)
            if not first:
                a = pd.concat([a, data], ignore_index=True)
            else:
                first = False
                a = data

        a.to_csv(path_or_buf='../'+frm+too+'.csv', header=False)
    else:
        a = pd.read_csv('../'+frm+too+'.csv', header=None, low_memory=False, dtype={
                           1: float}, usecols=[1])
    return a
