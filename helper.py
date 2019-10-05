import pandas as pd
import glob
from tqdm import tqdm
from multiprocessing import Pool
from new_data import download_new
len_df = 0
files_ = []


def load_df(ind, filename):
    global len_df
    len_df += 1
    tqdm.pandas(desc="load csvs #" + str(ind) + ' ' + str(files_[ind]))

    data = pd.read_csv(filename, header=None, low_memory=True, dtype={0: str, 1: str,
                       3: float}, skiprows=2, na_values=0).progress_apply(lambda x: x)
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
    download_new()
    # multiprocessing version of load_dfs
    for n, i in enumerate(files):
        if i.split('/')[1].split('.')[0] == '20190927':
            del files[n]  # remove wonky day's data
    frm = files[0].split('/')[1].split('.')[0]
    too = files[-1].split('/')[1].split('.')[0]

    files.reverse()
    print('backtest dates: ' + frm + '-' + too)
    global files_
    files_ = files
    if 1 == 1 or not glob.glob('../loaded' + frm + too + '.csv'):
        with Pool(processes=8) as pool:
            df_list = (pool.starmap(load_df, enumerate(files)))
            tqdm.pandas(desc="concat csvs")
            combined = pd.concat(df_list, ignore_index=True).progress_apply(lambda x: x) # apply dummy lambda fn to call tqdm.pandas()
            combined.to_csv(path_or_buf='../loaded' +
                            frm + too + '.csv', header=False)
    else:
        combined = pd.read_csv('../loaded' + frm + too + '.csv', header=None,
                               low_memory=False, dtype={1: float}, usecols=[0, 1], skiprows=2, na_values=0)
    print('loaded ' + str(combined.shape[0]) + ' ticks of data')
    return combined
