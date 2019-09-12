import numpy as np

import pandas as pd
from math import floor
import datetime
import requests
from engines import BitmexTrader, BinanceTrader, RobinhoodTrader, AlpacaTrader
import threading


class renko:
    def __init__(self, plot, j_backtest, fast, slow, signal_l, to_trade, strategy):

        self.trade = BitmexTrader(trade=to_trade, leverage=3, tp=0.5, test=False)
        self.j_backtest = j_backtest
        self.fast = int(fast)
        self.slow = int(slow)
        self.signal_l = int(signal_l)
        self.source_prices = []
        self.renko_prices = []
        self.renko_directions = []
        self.plot = plot
        self.end_backtest = datetime.datetime.now()
        self.strategy = strategy
        if self.plot:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches

    def set_brick_size(self, HLC_history=None, auto=True, brick_size=10.0):
        if auto:
            self.brick_size = self.__get_optimal_brick_size(
                HLC_history.iloc[:, [0, 1, 2]])
        else:
            self.brick_size = brick_size
        return self.brick_size

    def __renko_rule(self, last_price):
        gap_div = int(
            float(last_price - self.renko_prices[-1]) / self.brick_size)
        is_new_brick = False
        start_brick = 0
        num_new_bars = 0

        if gap_div != 0:
            if (gap_div > 0 and (self.renko_directions[-1] > 0 or self.renko_directions[-1] == 0)) or (gap_div < 0 and (self.renko_directions[-1] < 0 or self.renko_directions[-1] == 0)):
                num_new_bars = gap_div
                is_new_brick = True
                start_brick = 0
            elif np.abs(gap_div) >= 2:
                num_new_bars = gap_div
                num_new_bars -= np.sign(gap_div)
                start_brick = 2
                is_new_brick = True
                self.renko_prices.append(
                    self.renko_prices[-1] + 2 * self.brick_size * np.sign(gap_div))
                self.renko_directions.append(np.sign(gap_div))

            if is_new_brick:
                # add each brick
                for d in range(start_brick, np.abs(gap_div)):
                    self.renko_prices.append(
                        self.renko_prices[-1] + self.brick_size * np.sign(gap_div))
                    self.renko_directions.append(np.sign(gap_div))

        return num_new_bars

    def build_history(self, prices, timestamps):
        if len(prices) > 0:
            self.source_prices = prices
            self.renko_prices.append(prices.iloc[-1].values)
            #self.times.append(timestamps.iloc[-1].values)
            self.renko_directions.append(0)

            for p in self.source_prices[1:].values:
                self.__renko_rule(p)

        return len(self.renko_prices)

    def do_next(self, last_price):
        if len(self.renko_prices) == 0:
            self.source_prices.append(last_price)
            self.renko_prices.append(last_price)
            self.renko_directions.append(0)
            return 1
        else:
            self.source_prices.append(last_price)
            return self.__renko_rule(last_price)

    def get_renko_prices(self):
        return self.renko_prices

    def get_renko_directions(self):
        return self.renko_directions

    def plot_renko(self, col_up='g', col_down='r'):
        if self.plot:

            plt.ion()
            self.fig, self.ax = plt.subplots(3)
            self.fig.set_size_inches(18.5, 10.5)
            self.fig.savefig('test2png.png', dpi=100)
            self.ax[0].set_title('Renko chart')
            self.ax[0].set_xlabel('Renko bars')
            self.ax[0].set_ylabel('Price')
            self.ax[1].set_title('Indicators')
            self.ax[1].set_xlabel('Renko bars')
            self.ax[1].set_ylabel('Price')
            self.ax[2].set_title('Profit')
            self.ax[2].set_xlabel('Renko bars')
            self.ax[2].set_ylabel('Profit_btc')
            plt.show()

        self.last_timestamp = datetime.datetime(
            year=2018, month=7, day=12, hour=7, minute=9, second=33)  # random day in the past to make sure all data gets loaded as backtest

        self.ys = []
        self.xs = []
        self.lll = 0
        self.prices = []
        self.lim_x_max = 0
        self.lim_x_min = 0
        self.lim_y_min = 0
        self.lim_y_max = 0
        self.next_brick = 0
        self.backtest = True
        self.backtest_bal_usd = 500
        self.backtest_fee = 0.00075
        self.backtest_slippage = 12*0.5  # ticks*tick_size=$slip
        self.w = 1
        self.l = 1
        self.runs = 0
        self.balances = []
        self.ff = True
        self.long = False
        self.short = False
        self.open = 0
        self.profit = 0
        self.lim_x_max = len(self.renko_prices) + 15
        self.lim_y_max = np.max(self.renko_prices) + 3.0 * self.brick_size
        self.lim_y_min = np.min(self.renko_prices) - 3.0 * self.brick_size
        self.first = True
        if self.plot:
            self.ax[0].set_xlim(0.0,
                                len(self.renko_prices) + 1.0)
            self.ax[0].set_ylim(np.min(self.renko_prices) - 3.0 * self.brick_size,
                                np.max(self.renko_prices) + 3.0 * self.brick_size)
            self.ax[1].set_xlim(0.0,
                                len(self.renko_prices) + 1.0)
            self.ax[1].set_ylim(-100, 100)
            self.ax[2].set_xlim(0.0,
                                len(self.renko_prices) + 1.0)
            self.ax[2].set_ylim(-0.0005, 0.0005)
            plt.show(block=False)
        for i in range(1, len(self.renko_prices)):
            self.col = col_up if self.renko_directions[i] == 1 else col_down
            self.x = i
            self.y = self.renko_prices[i] - \
                self.brick_size if self.renko_directions[i] == 1 else self.renko_prices[i]
            self.last = self.renko_prices[-1]
            self.aaa = self.last
            self.animate()
        self.last = self.renko_prices[-1]

        '''
        for a in range(10):
            self.ax[0].set_xlim(0.0, len(self.renko_prices) + (a+2))
            self.ax[0].set_ylim(np.min(self.renko_prices) - 3.0 * self.brick_size,
                        np.max(self.renko_prices) + 3.0*(a+1) * self.brick_size)
            self.add_to_plot(12344+a*32)
        '''

        self.backtest = False
        while True:
            self.check_for_new()
            # time.sleep(1)

    def check_for_new(self):

        data = requests.get('http://132.198.249.205:4444/quote?symbol=XBTUSD').json()
        for key in data:
            if datetime.datetime.strptime(key['timestamp'].replace('T', ''), '%Y-%m-%d%H:%M:%S.%fZ') > self.last_timestamp:
                self.add_to_plot(float(key['bidPrice']))
                self.last_timestamp = datetime.datetime.strptime(
                    key['timestamp'].replace('T', ''), '%Y-%m-%d%H:%M:%S.%fZ')
            #print('finished loading backtest data, proceeding to live, backtest profit: $' + str(self.profit*self.aaa))

    def add_to_plot(self, price):
        self.aaa = price
        self.prices.append(price)
        '''
        try:
            print (str(self.last_timestamp))
        except:
            pass
        '''
        # print('last price: ' + str(self.ys[-1]), 'current: ' + str(price), "need: " + str(self.brick_size + self.ys[-1]), 'or: ' + str(self.ys[-1] - self.brick_size))
        # plt.title('last price: ' + str(self.ys[-1]) + ' current: ' + str(price) + " need: " + str(self.brick_size + self.ys[-1]) + ' or: ' + str(self.ys[-1] - self.brick_size))
        if price > self.brick_size + self.ys[-1]:
            for a in range(floor((price - self.ys[-1]) / self.brick_size)):
                if self.plot:
                    self.ax[0].set_xlim(self.lim_x_min, self.lim_x_max + 1)
                    self.ax[1].set_xlim(self.lim_x_min, self.lim_x_max + 1)
                    self.ax[2].set_xlim(self.lim_x_min, self.lim_x_max + 1)
                    self.ax[0].set_ylim(
                        self.lim_y_min, self.lim_y_max + self.brick_size)

                self.x = self.x + 1
                self.y = self.y + self.brick_size
                self.col = 'g'
                self.animate()
                self.lim_x_max = self.lim_x_max + 1
                self.lim_y_max = self.lim_y_max + self.brick_size
                self.last = price
        elif price < self.ys[-1] - 2 * self.brick_size:
            for i in range(floor((self.ys[-1] - price) / self.brick_size)):
                if self.plot:
                    #print(self.lim_y_max, self.lim_y_min)
                    self.ax[0].set_xlim(self.lim_x_min, self.lim_x_max + 1)
                    self.ax[1].set_xlim(self.lim_x_min, self.lim_x_max + 1)
                    self.ax[2].set_xlim(self.lim_x_min, self.lim_x_max + 1)
                    self.ax[0].set_ylim(self.lim_y_min -
                                        self.brick_size, self.lim_y_max)

                self.x = self.x + 1
                self.y = self.y - self.brick_size
                self.col = 'r'
                self.animate()
                self.lim_x_max = self.lim_x_max + 1
                self.lim_y_min = self.lim_y_min - self.brick_size
                self.last = price

    def animate(self):
        self.lll = self.lll + 1
        # - self.brick_size to get the open price of the brick
        self.ys.append(self.y - self.brick_size)
        self.xs.append(self.x)
        # print(self.x, self.y)
        if self.next_brick == 1:
            self.col = 'b'
        elif self.next_brick == 2:
            self.col = 'y'

        self.balances.append(self.profit)
        if self.plot:
            self.ax[0].add_patch(
                patches.Rectangle(
                    (self.x, self.y),   # (x,y)
                    1.0,     # width
                    self.brick_size,  # height
                    facecolor=self.col
                )
            )
            self.ax[1].plot(self.xs, self.macd())
            self.ax[1].plot(self.xs, self.sma())

            try:
                self.ax[2].set_ylim(min(self.balances) * 2,
                                    max(self.balances) * 2)
            except:
                pass

            self.ax[2].plot(self.xs, self.balances)

        self.calc_indicator()
        if self.plot:
            plt.draw()
            plt.pause(0.0000001)

    def ma(self):
        fast_ma = pd.DataFrame(self.ys).rolling(window=self.fast).mean()
        slow_ma = pd.DataFrame(self.ys).rolling(window=self.slow).mean()
        return fast_ma.values, slow_ma.values

    def macd(self):
        fast, slow = self.ma()
        macda = []
        for n, i in enumerate(fast):
            macda.append(i - slow[n])

        return macda

    def sma(self):
        return (pd.DataFrame(self.macd()).rolling(window=self.signal_l).mean()).values

    def cross(self, a, b):
        try:
            if (a[-2] > b[-2] and b[-1] > a[-1]) or (b[-2] > a[-2] and a[-1] > b[-1]) or (a[-2] > b[-2] and b[-1] == a[-1]) or (b[-2] > a[-2] and b[-1] == a[-1]):
                return True
            return False
        except:
            return False

    def close_short(self, price):
        self.profit = self.profit + \
            (1 / self.pricea - 1 / (self.open)) * self.backtest_bal_usd
        self.profit = self.profit - \
            (1 / self.pricea - 1 / (self.open)) * \
            self.backtest_bal_usd * self.backtest_fee
        self.backtest_bal_usd = self.backtest_bal_usd + floor(((1 / self.pricea - 1 / (self.open)) * self.backtest_bal_usd - (1 / self.pricea - 1 / (self.open))*self.backtest_bal_usd*self.backtest_fee) * self.pricea)
        try:
            per = ((self.w+self.l)-self.w)/(self.w+self.l)
        except:
            per = 0
        print('trade: $' + str(((1 / self.pricea - 1 / (self.open)) * self.backtest_bal_usd - (1 / self.pricea - 1 / (self.open)) * self.backtest_bal_usd * self.backtest_fee)*self.pricea),'net BTC: ' + str(self.profit), 'closed at: ' + str(self.pricea), 'profitable?: ' + str('yes') if price < self.open else str('no'), 'balance: $' + str(self.backtest_bal_usd), 'percentage profitable ' + str(round(per*100,3))+'%')
        if price < self.open:
            self.w = self.w + 1
        else:
            self.l = self.l + 1

    def close_long(self, price):
        if price > self.open:
            self.w = self.w + 1
        else:
            self.l = self.l + 1
        self.profit = self.profit + (1 / self.open - 1 / (self.pricea)) * self.backtest_bal_usd
        fee_btc = (1 / self.open - 1 / (self.pricea)) * self.backtest_bal_usd * self.backtest_fee
        self.profit = self.profit - fee_btc
        self.backtest_bal_usd = self.backtest_bal_usd + floor(((1 / self.open - 1 / (self.pricea)) * self.backtest_bal_usd - (1 / self.open - 1 / (self.pricea))*self.backtest_bal_usd*self.backtest_fee) * self.pricea)
        try:
            per = ((self.w+self.l)-self.w)/(self.w+self.l)
        except:
            per = 0
        print('trade: $' + str(((1 / self.open - 1 / (self.pricea)) * self.backtest_bal_usd - (1 / self.open - 1 / (self.pricea)) * self.backtest_bal_usd * self.backtest_fee)*self.pricea), 'net BTC: ' + str(self.profit), 'closed at: ' + str(self.pricea), 'profitable?: ' + str('no') if price < self.open else str('yes'), 'balance $' + str(self.backtest_bal_usd), 'percentage profitable: ' +  str(round(per*100,3))+'%')

    def calc_indicator(self):
        if self.strategy == 0:
            self.pricea = self.ys[-1]
            if self.cross(self.macd(), self.sma()) and self.macd()[-1] > self.sma()[-1] and not self.long:
                self.long = True
                self.short = False
                if self.runs > 0:
                    self.close_short(self.pricea)

                if self.end_backtest <= self.last_timestamp and not self.j_backtest:
                    threading.Thread(target=self.trade.buy_long, args=(
                        "BITMEX", "XBT-USD", self.pricea, )).start()
                    if self.ff:
                        print ('net backtest profit: $' + self.backtest_bal_usd + ' with $' + str(self.backtest_slippage) + ' of slippage per trade')
                        print ('proceeding to live...')
                        self.backtest_bal_usd = 300
                        self.profit = 0
                        self.ff = False
                    print('BUY at: ' + str(self.pricea),
                          str(datetime.datetime.now()), 'slip: ' + str())
                else:
                    self.profit = self.profit - ((self.backtest_bal_usd/self.pricea)*self.backtest_fee)
                    print('backtest BUY at: ' + str(self.pricea), 'amount: ' + str(self.backtest_bal_usd), 'fee: $' + str(round(((self.backtest_bal_usd/self.pricea)*self.backtest_fee*self.pricea)[0],3)))
                self.open = self.pricea - self.backtest_slippage
                self.next_brick = 1
                self.runs = self.runs + 1
            elif self.cross(self.macd(), self.sma()) and self.sma()[-1] > self.macd()[-1] and not self.short:
                self.short = True
                self.long = False
                if self.runs > 0:
                    self.close_long(self.pricea)

                if self.end_backtest <= self.last_timestamp and not self.j_backtest:
                    threading.Thread(target=self.trade.sell_short,
                                     args=("BITMEX", "XBT-USD", self.pricea, )).start()
                    if self.ff:
                        print ('net backtest profit: $' + self.backtest_bal_usd + ' with $' + str(self.backtest_slippage) + ' of slippage per trade')
                        print ('proceeding to live...')
                        self.backtest_bal_usd = 300
                        self.profit = 0
                        self.ff = False
                    print('SELL at: ' + str(self.pricea),
                          str(datetime.datetime.now()))
                else:
                    self.profit = self.profit - ((self.backtest_bal_usd/self.pricea)*self.backtest_fee)
                    print('backtest SELL at: ' + str(self.pricea), 'amount: ' + str(self.backtest_bal_usd), 'fee: $' + str(round(((self.backtest_bal_usd/self.pricea)*self.backtest_fee*self.pricea)[0],3)))
                self.open = self.pricea + self.backtest_slippage
                self.next_brick = 2
                self.runs = self.runs + 1
            else:
                self.next_brick = 0
