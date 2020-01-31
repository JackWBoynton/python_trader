import pandas as pd
from helper import load_dfs_mult
# block data into 5 day segments for effecient memory analysis

BLOCKSIZE = 5

def get_data(days):
    final = [days[i * BLOCKSIZE:(i + 1) * BLOCKSIZE] for i in range((len(days) + BLOCKSIZE - 1) // BLOCKSIZE )]
    for i in final[::-1]:
        yield pd.DataFrame(load_dfs_mult("XBTUSD",files=i,location="../"))
    if len(days) % 5 != 0:
        yield pd.DataFrame(load_dfs_mult("XBTUSD",files=days,location="../"))

