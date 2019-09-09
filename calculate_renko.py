
import pandas as pd

import pyrenko
import helper as helper
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fast", nargs=3, type=int)
parser.add_argument("-t", "--trade")
args = parser.parse_args()

print('fast ma length: {}'.format(args.fast[0]), 'slow ma length: {}'.format(args.fast[1]), 'signal length: {}'.format(args.fast[2]))
sta = sorted(glob.glob('/home/jayce/201909*.csv'))
print('trade: ' + str(True) if args.trade else str(False))
data = pd.DataFrame(helper.load_dfs('XBTU19', sta,filenames=sta).values)

renko_obj = pyrenko.renko(plot=False, j_backtest=False, fast=int(args.fast[0]), slow=int(args.fast[1]), signal_l=int(args.fast[2]), to_trade=True if args.trade else False)
renko_obj.set_brick_size(brick_size=25, auto=False)
renko_obj.build_history(prices=data)
renko_obj.plot_renko()
