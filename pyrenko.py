'''
python3
renko brick calculation python implementation
Jack Boynton 2019
'''
from tqdm import tqdm
import numpy as np
import pandas as pd
from math import floor
import datetime
import requests
from data import new_trade
from engines import BitmexTrader, BinanceTrader, RobinhoodTrader, AlpacaTrader
import threading
from calculate_pred import main as pred
import statistics


class renko:
    def __init__(self, plot, j_backtest, fast, slow, signal_l, to_trade, strategy):

        self.trade = BitmexTrader(
            trade=True, leverage=10, tp=0.5, test=to_trade)
        self.j_backtest = j_backtest
        self.fast = int(fast)
        self.slow = int(slow)
        self.signal_l = int(signal_l)
        self.source_prices = []
        self.returns = []
        self.trades_ = []
        self.renko_prices = []
        self.renko_directions = []
        self.plot = plot  # unused
        self.timestamps = []
        self.macdaa = []
        self.smaa = []
        self.act_timestamps = []
        self.end_backtest = datetime.datetime.now()
        self.strategy = strategy
        self.use_ml = True

    def set_brick_size(self, HLC_history=None, auto=True, brick_size=10.0):
        if auto:
            self.brick_size = self.__get_optimal_brick_size(
                HLC_history.iloc[:, [0, 1, 2]])
        else:
            self.brick_size = brick_size
        return self.brick_size

    def __renko_rule(self, last_price, ind):
        # determines if should plot new bricks
        # returns number of new bricks to plot
        # print(last_price,ind)
        try:
            gap_div = int(
                float(last_price - self.renko_prices[-1]) / self.brick_size)
        except Exception:
            gap_div = 0
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
                self.act_timestamps.append(self.timestamps[ind])
                self.renko_directions.append(np.sign(gap_div))
            if is_new_brick:
                # add each brick
                for d in range(start_brick, np.abs(gap_div)):
                    self.renko_prices.append(
                        self.renko_prices[-1] + self.brick_size * np.sign(gap_div))
                    self.act_timestamps.append(self.timestamps[ind])
                    self.renko_directions.append(np.sign(gap_div))
        return num_new_bars

    def build_history(self, prices, timestamps):
        # builds backtest bricks
        if len(prices) > 0:
            self.timestamps = prices[0].values
            self.source_prices = pd.DataFrame(prices[2].values)
            self.renko_prices.append(prices[2].values[-1])
            self.act_timestamps.append(prices[0].values[-1])
            self.renko_directions.append(0)

            for n, p in tqdm(enumerate(self.source_prices[1:].values), total=len(self.source_prices[1:].values), desc='build renko'):  # takes long time
                # print(type(p),p)
                self.__renko_rule(p, n)  # performs __renko_rule on each price tick

            # map(lambda x: self.__renko_rule(x[1], x[0]), enumerate(self.source_prices[1:].values))
        return len(self.renko_prices)

    def do_next(self, last_price):
        # function that is used to plot live data
        # calls __renko_rule on each new live price tick
        last_price = float(last_price)
        if len(self.renko_prices) == 0:
            self.source_prices.append(last_price)
            self.renko_prices.append(last_price)
            self.renko_directions.append(0)
            return 1
        else:
            self.source_prices.append(last_price)
            return self.__renko_rule(last_price, 1)

    def get_renko_prices(self):
        return self.renko_prices

    def get_renko_directions(self):
        return self.renko_directions

    def plot_renko(self, col_up='g', col_down='r'):
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
        self.backtest_bal_usd = 0.005
        self.init = self.backtest_bal_usd
        self.backtest_fee = 0.00075  # 0.11%
        self.backtest_slippage = 12 * 0.5  # ticks*tick_size=$slip
        self.leverage = 10
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
        for i in range(1, len(self.renko_prices)):
            self.col = col_up if self.renko_directions[i] == 1 else col_down
            self.x = i
            self.y = self.renko_prices[i] - \
                self.brick_size if self.renko_directions[i] == 1 else self.renko_prices[i]
            self.last = self.renko_prices[-1]
            self.aaa = self.last
            self.animate(i)
        self.last = self.renko_prices[-1]
        self.backtest = False
        self.bricks = 0

        self.source_prices = []
        # self.ys = [0]
        self.l = 1
        self.w = 1
        #print(self.returns)
        #self.returns = map(lambda x: x*100, self.returns)
        sr = pd.DataFrame(self.returns[2:]).cumsum()
        sra = (sr - sr.shift(1))/sr.shift(1)
        srb = sra.mean()/sra.std() * np.sqrt(252)
        print('net backtest profit: BTC ' + str(self.backtest_bal_usd - self.init) + ' :: ' + str(round(((self.backtest_bal_usd-self.init)/self.init)*100, 3)) + ' percent')
        print('net backtest profit: BTC ' + str(self.backtest_bal_usd), 'max drawdown: ' + str(round(min(self.trades_), 8)) + ' BTC', 'max trade: ' + str(round(max(self.trades_), 8)) + ' BTC', 'average: ' + str(round(statistics.mean(self.trades_), 8)) + ' BTC', 'SR: ' + str(round(srb[0], 5)))
        while True:
            # starts live trading
            self.check_for_new()

    def check_for_new(self):
        # connects to hosted BITMEX delta server running in nodejs on port 4444
        data = requests.get(
            'http://132.198.249.205:4444/quote?symbol=XBTUSD').json()
        for key in data:
            if datetime.datetime.strptime(key['timestamp'].replace('T', ''), '%Y-%m-%d%H:%M:%S.%fZ') > self.last_timestamp:
                self.add_to_plot(float(key['bidPrice']), self.do_next(
                    np.array(float(key['bidPrice']), dtype=float)))
                print(str(float(key['bidPrice'])) + ' brick: ' + str(self.last) + ' sma: ' + str(self.smaa[-1]) + ' macd: ' + str(
                    self.macdaa[-1]) + ' len: ' + str(len(self.ys)) + ' bricks: ' + str(self.bricks), end="\r")
                self.last_timestamp = datetime.datetime.strptime(
                    key['timestamp'].replace('T', ''), '%Y-%m-%d%H:%M:%S.%fZ')

    def add_to_plot(self, price, bricks):
        self.aaa = self.last
        self.bricks = bricks
        self.prices.append(self.last)
        for i in range(1, bricks + 1):
            self.x = self.x + i
            self.y = self.renko_prices[-(bricks + 2) - i] - self.brick_size if self.renko_directions[-(
                bricks + 2) - i] == 1 else self.renko_prices[-(bricks + 2) - i]
            self.last = self.renko_prices[-(bricks + 2) - i]
            self.aaa = self.last
            self.animate(1)
        self.last = self.renko_prices[-1]

    def animate(self, i):
        self.lll += 1
        self.ys.append(self.y)  # all bricks for indicator calculation
        self.xs.append(self.x)  # num bars
        if self.next_brick == 1:
            self.col = 'b'
        elif self.next_brick == 2:
            self.col = 'y'
        self.balances.append(self.profit)
        self.calc_indicator(i)  # calculates given indicator

    def ma(self):
        # calculates simple moving averages on brick prices
        fast_ma = pd.DataFrame(self.ys).rolling(window=self.fast).mean()
        slow_ma = pd.DataFrame(self.ys).rolling(window=self.slow).mean()
        return fast_ma.values, slow_ma.values

    def macd(self):
        # calculated moving average convergence divergence on brick prices
        fast, slow = self.ma()
        macda = []
        for n, i in enumerate(fast):
            macda.append(i - slow[n])
        self.macdaa = macda
        return macda

    def sma(self):
        # simple moving average to compare against macd
        self.smaa = (pd.DataFrame(self.macd()).rolling(
            window=self.signal_l).mean()).values
        return (pd.DataFrame(self.macd()).rolling(window=self.signal_l).mean()).values

    def cross(self, a, b):
        # determines if signal price and macd cross or had crossed one brick ago
        try:
            if (a[-2] > b[-2] and b[-1] > a[-1]) or (b[-2] > a[-2] and a[-1] > b[-1]) or (a[-2] > b[-2] and b[-1] == a[-1]) or (b[-2] > a[-2] and b[-1] == a[-1]):
                return True
            return False
        except Exception:
            return False

    def close_short(self, price):
        # calculates profit on close of short trade
        net = round(((1 / self.pricea - 1 / (self.open)) * floor(self.risk*self.open)*self.leverage), 8)
        self.profit += net
        fee = round((self.risk*self.leverage * self.backtest_fee), 8)
        fee += round((self.risk*self.leverage * self.backtest_fee), 8)
        self.profit -= fee
        print(type(net-fee))
        self.backtest_bal_usd += round((net - fee), 8)
        ret = round((net - fee), 8)/self.risk
        self.returns.append(ret)
        try:
            per = ((self.w + self.l) - self.l) / (self.w + self.l)
        except Exception:
            per = 0
        self.trades_.append(round((net-fee), 8))
        print('trade: BTC ' + str(round((net - fee), 8)), 'net BTC: ' + str(round(self.profit, 8)),
              'closed at: ' + str(self.pricea), 'profitable?: ' + str('yes') if price < self.open else str('no'), 'balance: BTC ' + str(self.backtest_bal_usd), 'percentage profitable ' + str(round(per * 100, 3)) + '%', 'w:' + str(self.w), 'l:' + str(self.l))
        if price < self.open:
            self.w += 1
        else:
            self.l += 1

    def close_long(self, price):
        # calculates profit on close of long trade
        if price > self.open:
            self.w += 1
        else:
            self.l += 1
        net = round(((1 / self.open - 1 / (self.pricea)) * floor(self.risk*self.open)*self.leverage), 8)
        self.profit += net
        fee = round((self.risk*self.leverage * self.backtest_fee), 8)
        fee += round((self.risk*self.leverage * self.backtest_fee), 8)
        self.profit -= fee
        print(type(net-fee))
        self.backtest_bal_usd += round((net - fee), 8)
        ret = round((net - fee), 8)/self.risk
        self.returns.append(ret)
        try:
            per = ((self.w + self.l) - self.l) / (self.w + self.l)
        except Exception:
            per = 0
        self.trades_.append(round((net - fee), 8))
        print('trade: BTC ' + str(round((net - fee), 8)), 'net BTC: ' + str(round(self.profit, 8)),
              'closed at: ' + str(self.pricea), 'profitable?: ' + str('no') if price < self.open else str('yes'), 'balance $' + str(self.backtest_bal_usd), 'percentage profitable: ' + str(round(per * 100, 3)) + '%', 'w:' + str(self.w), 'l:' + str(self.l))

    def calc_indicator(self, ind):
        # calculates indicator
        if 0 == 0: # can add more indicators by expanding if condition:
            self.pricea = self.y
            if self.cross(self.macd(), self.sma()) and self.macd()[-1] > self.sma()[-1] and not self.long:
                self.long = True
                self.short = False
                if self.runs > 0:
                    self.close_short(self.pricea)
                    if self.long:
                        side = 0
                    elif self.short:
                        side = 1
                    if len(self.renko_prices) > 10 and len(self.macd()) > 10:
                        # write trades to file
                        new_trade(past_bricks=self.ys_open, price_open=self.open, price_close=self.pricea, side=side, macd_open=self.macd_open, macd_close=self.macd()[-1], sma_open=self.sma_open, sma_close=self.sma()[-1], time_open=self.open_time, time_close=self.act_timestamps[ind])
                if self.end_backtest <= self.last_timestamp and not self.j_backtest and len(self.ys) > 35:
                    predi = pred(self.ys[-10:], self.macd()[-10:], self.sma()[-10:], self.pricea)
                    threading.Thread(target=self.trade.buy_long, args=("BITMEX", "XBT-USD", self.pricea, self.pricea, predi, )).start()
                    if self.ff:
                        print('net backtest profit: BTC ' + str(self.backtest_bal_usd) +
                              ' with $' + str(self.backtest_slippage) + ' of slippage per trade', 'max drawdown: ' + str(min(self.trades_)), 'max trade: ' + str(max(self.trades_)), 'average: ' + str(statistics.mean(self.trades_)))
                        print('proceeding to live...')
                        self.backtest_bal_usd = self.init
                        self.profit = 0
                        self.ff = False

                    print('BUY at: ' + str(self.pricea),
                          str(datetime.datetime.now()), 'pred: ' + str(pred(self.ys[-10:], self.macd()[-10:], self.sma()[-10:], self.pricea)))
                else:
                    if ind != 1:
                        sss = self.act_timestamps[ind]
                    else:
                        sss = 'undef'
                    if len(self.macd()) > 10 and len(self.sma()) > 10 and len(self.ys) > 10:
                        if self.use_ml:
                            predi = pred(self.ys[-10:], self.macd()[-10:], self.sma()[-10:], self.pricea)
                        else:
                            predi = 1
                        self.risk = self.backtest_bal_usd * predi
                        print('backtest BUY at: ' + str(self.pricea), 'time: ' + str(sss), 'amount: ' + str(self.risk),
                              'fee: $' + str(round(((floor(self.risk*self.pricea)*self.leverage / self.pricea) * self.backtest_fee * self.pricea), 3)), 'pred: ' + str(predi))

                self.open = self.pricea
                self.open_time = self.act_timestamps[ind]
                self.macd_open = self.macd()[-10:]
                self.ys_open = self.ys[-10:]
                self.sma_open = self.sma()[-10:]
                self.next_brick = 1
                self.runs += 1
            elif self.cross(self.macd(), self.sma()) and self.sma()[-1] > self.macd()[-1] and not self.short:
                self.short = True
                self.long = False
                if self.runs > 0:
                    self.close_long(self.pricea)
                    if self.long:
                        side = 0
                    elif self.short:
                        side = 1
                    if len(self.renko_prices) > 10 and len(self.macd()) > 10 and len(self.ys) > 10:
                        # write trades to file
                        new_trade(past_bricks=self.ys_open, price_open=self.open, price_close=self.pricea, side=side, macd_open=self.macd_open, macd_close=self.macd()[-1], sma_open=self.sma_open, sma_close=self.sma()[-1], time_open=self.open_time, time_close=self.act_timestamps[ind])

                if self.end_backtest <= self.last_timestamp and not self.j_backtest and len(self.ys) > 35:
                    predi = pred(self.ys[-10:], self.macd()[-10:], self.sma()[-10:], self.pricea)
                    threading.Thread(target=self.trade.sell_short, args=("BITMEX", "XBT-USD", self.pricea, self.pricea, predi, )).start()
                    if self.ff:
                        print('net backtest profit: BTC ' + str(self.backtest_bal_usd) +
                              ' with $' + str(self.backtest_slippage) + ' of slippage per trade', 'max drawdown: ' + str(min(self.trades_)), 'max trade: ' + str(max(self.trades_)), 'average: ' + str(statistics.mean(self.trades_)))
                        print('proceeding to live...')
                        self.backtest_bal_usd = self.init
                        self.profit = 0
                        self.ff = False
                    if len(self.macd()) > 10 and len(self.sma()) > 10 and len(self.ys) > 10:
                        print('SELL at: ' + str(self.pricea),
                              str(datetime.datetime.now()), 'pred: ' + str(pred(self.ys[-10:], self.macd()[-10:], self.sma()[-10:], self.pricea)))

                else:
                    if ind != 1:
                        sss = self.act_timestamps[ind]
                    else:
                        sss = 'undef'
                    if len(self.macd()) > 10 and len(self.sma()) > 10 and len(self.ys) > 10:
                        if self.use_ml:
                            predi = pred(self.ys[-10:], self.macd()[-10:], self.sma()[-10:], self.pricea)
                        else:
                            predi = 1
                        self.risk = self.backtest_bal_usd * predi
                        print('backtest SELL at: ' + str(self.pricea), 'time: ' + str(sss), 'amount: ' + str(self.risk),
                              'fee: $' + str(round(((floor(self.risk*self.pricea)*self.leverage / self.pricea) * self.backtest_fee * self.pricea), 3)), 'pred: ' + str(predi))

                self.open = self.pricea
                self.open_time = self.act_timestamps[ind]
                self.macd_open = self.macd()[-10:]
                self.ys_open = self.ys[-10:]
                self.sma_open = self.sma()[-10:]
                self.next_brick = 2
                self.runs += 1
            else:
                self.next_brick = 0
