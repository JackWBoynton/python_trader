import pandas as pd
from helper import load_dfs_mult
# block data into 5 day segments for effecient memory analysis

BLOCKSIZE = 5

def get_data(days):
    #print(days)
    last = 0
    for i in range(len(days)//BLOCKSIZE):
        #print(days[last:i])
        yield pd.DataFrame(load_dfs_mult("XBTUSD",files=days[last:last+5],location="../"))
        last += 5
    if len(days) % 5 != 0:
        yield pd.DataFrame(load_dfs_mult("XBTUSD",files=days[last:-1],location="../"))

