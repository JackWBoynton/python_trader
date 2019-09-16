
import pandas as pd

import pyrenko
import helper as helper
import glob
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fast", nargs=3, type=int)
parser.add_argument("-t", "--trade")
parser.add_argument('-r', '--tr', type=str)
parser.add_argument('-b', '--brick_size', type=int)
parser.add_argument('-d', '--days', type=int)
args = parser.parse_args()

print('fast ma length: {}'.format(args.fast[0]), 'slow ma length: {}'.format(args.fast[1]), 'signal length: {}'.format(args.fast[2]))
#time = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d')
#string = str(time.split('-')[0]) + str(time.split('-')[0]) + str(int(time.split('-')[2])-1)
time = datetime.date.today() - datetime.timedelta(days=1)
sta = []
for i in range(args.days):
    sta.append('../../' + datetime.datetime.strftime(time-datetime.timedelta(days=i), "%Y%m%d")+'.csv')
print (sta)
print('starting to load csv backtest data... days: ' + str(args.days))
data = pd.DataFrame(helper.load_dfs_mult('XBTU19', files=sta))

print ('finished loading csv backtest data... starting renko brick calculation')
renko_obj = pyrenko.renko(plot=False, j_backtest=False, fast=int(args.fast[0]), slow=int(args.fast[1]), signal_l=int(args.fast[2]), to_trade=False, strategy=0 if args.tr == 'macd' else 1)
renko_obj.set_brick_size(brick_size=args.brick_size, auto=False)
renko_obj.build_history(prices=data, timestamps=[''])
renko_obj.plot_renko()
