'''
Python3
Main running script -- for pyrenko live brick calculation and indicator calculation
Jack Boynton 2019
'''
import pandas as pd
import pyrenko
import helper as helper
import sys
import datetime
import argparse
import matplotlib.pyplot as plt
import time
import calendar
import matplotlib

parser = argparse.ArgumentParser()
parser.add_argument("fast", nargs=3, type=int)
parser.add_argument("-t", "--trade", type=int)
parser.add_argument('-r', '--tr', type=str)
parser.add_argument('-b', '--brick_size', type=int)
parser.add_argument('-d', '--days', type=int)
parser.add_argument('-o', '--order_type', type=str)
parser.add_argument("-p",  "--plot", type=bool)
args = parser.parse_args()
if args.order_type and args.order_type == 'Market' or args.order_type == 'Limit':
    pass
else:
    print('must set order_type to market or limit')
    sys.exit(0)
args.trade = bool(args.trade)
print(args.trade)
print('fast ma length: {}'.format(args.fast[0]), 'slow ma length: {}'.format(
    args.fast[1]), 'signal length: {}'.format(args.fast[2]), 'ord_type: ' + str(args.order_type))
time = datetime.date.today() - datetime.timedelta(days=1) # cant get todays data until tomorrow
sta = []
for i in range(args.days):  # gets all date csv files in home directory
    sta.append('../' + datetime.datetime.strftime(time -
                                                  datetime.timedelta(days=i), "%Y%m%d") + '.csv')

print('starting to load csv backtest data... days: ' + str(args.days))

data = pd.DataFrame(helper.load_dfs_mult('XBTUSD', files=sta, location='../'))  # uses multiprocessing to parse huge csv datafiles
print('finished loading csv backtest data... starting renko brick calculation')
renko_obj = pyrenko.renko(plot=False, j_backtest=True, fast=int(args.fast[0]), slow=int(
    args.fast[1]), signal_l=int(args.fast[2]), to_trade=args.trade, strategy=0 if args.tr == 'macd' else 1, ordtype=args.order_type)
renko_obj.set_brick_size(brick_size=args.brick_size, auto=False)  # sets brick_size hyperparam in dollars
renko_obj.build_history(prices=data, timestamps=[''])  # builds renko backtest
trades = renko_obj.plot_renko()  # starts live renko brick calculation
# 2019-12-17D23:09:17.575367000 # sample timestamp from bitmex
if args.plot:
    macd_ = renko_obj.macd()
    fast, slow = renko_obj.ma()
    times = renko_obj.act_timestamps
    print(len(renko_obj.ys), len(macd_), len(renko_obj.act_timestamps)) # 204 204 205
    print(f"x:{renko_obj.act_timestamps[-2]},y:{macd_[-1]}")
    # takes an incredible amount of time bc graphing millions of price ticks
    p = "%Y-%m-%d%H:%M:%S.%f000"
    timestampss = []
    plt.figure(figsize=(20,20))
    for n, point in enumerate(data[1]):
        point = point.replace("D","")
        st = (datetime.datetime.strptime(point,p))
        timestampss.append(calendar.timegm(st.timetuple()))
    macd_timestamps = []
    for m, pt in enumerate(times[-len(macd_):]):
        pt = pt.replace("D","")
        ac = (datetime.datetime.strptime(pt,p))
        macd_timestamps.append(calendar.timegm(ac.timetuple()))
    #plt.plot(macd_timestamps, macd_)
    plt.plot(timestampss, data[2])
    plt.plot(macd_timestamps, slow)
    plt.plot(macd_timestamps, fast)
    for i in trades:
        if i[0] == 1:
            point = i[1].replace("D","")
            timestamp = (datetime.datetime.strptime(point,p))
            plt.scatter(calendar.timegm(timestamp.timetuple()),[i[2]], c="#00ff00")
        else:
            point = i[1].replace("D","")
            timestamp = (datetime.datetime.strptime(point,p))       
            plt.scatter(calendar.timegm(timestamp.timetuple()),[i[2]], c="#ff0000")

    plt.show()
