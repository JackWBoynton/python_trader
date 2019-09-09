
import pandas as pd

import pyrenko
import helper as helper
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fast", nargs=3, type=int)

args = parser.parse_args()

print('fast ma length: {args.fast[0]}', 'slow ma length: {args.fast[1]}', 'signal length: {args.fast[2]}')
sta = sorted(glob.glob('/home/jayce/201909*.csv'))

data = pd.DataFrame(helper.load_dfs('XBTU19', sta).values)

renko_obj = pyrenko.renko(plot=False, j_backtest=False, fast=int(args.fast[0]), slow=int(args.fast[1]), signal_l=int(args.fast[2]))
renko_obj.set_brick_size(brick_size=25, auto=False)
renko_obj.build_history(prices=data)
renko_obj.plot_renko()
