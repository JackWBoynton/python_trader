'''
Python3
Main running script -- for pyrenko live brick calculation and indicator calculation
Jack Boynton 2019
'''
import pandas as pd
import pyrenko
import helper as helper
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fast", nargs=3, type=int)
parser.add_argument("-t", "--trade")
parser.add_argument('-r', '--tr', type=str)
parser.add_argument('-b', '--brick_size', type=int)
parser.add_argument('-d', '--days', type=int)
args = parser.parse_args()

print('fast ma length: {}'.format(args.fast[0]), 'slow ma length: {}'.format(
    args.fast[1]), 'signal length: {}'.format(args.fast[2]))
time = datetime.date.today() - datetime.timedelta(days=1)
sta = []
for i in range(args.days):  # gets all date csv files in home directory
    sta.append('../' + datetime.datetime.strftime(time -
                                                  datetime.timedelta(days=i), "%Y%m%d") + '.csv')

print('starting to load csv backtest data... days: ' + str(args.days))
if len(sta) > 1:
    data = pd.DataFrame(helper.load_dfs_mult('XBTU19', files=sta))  # uses multiprocessing to parse huge csv datafiles
else:
    data = pd.DataFrame(helper.load_df(sta[0]))
print('finished loading csv backtest data... starting renko brick calculation')
renko_obj = pyrenko.renko(plot=False, j_backtest=False, fast=int(args.fast[0]), slow=int(
    args.fast[1]), signal_l=int(args.fast[2]), to_trade=False, strategy=0 if args.tr == 'macd' else 1)
renko_obj.set_brick_size(brick_size=args.brick_size, auto=False)  # sets brick_size hyperparam in dollars
renko_obj.build_history(prices=data, timestamps=[''])  # builds renko backtest
renko_obj.plot_renko()  # starts live renko brick calculation
